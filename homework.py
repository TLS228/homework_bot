import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import AbsentEnvironmentVariable, ResponseNot200

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('program.log', mode='w')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяем доступность переменных окружения."""
    tokens = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_tokens = [token for token in tokens if not globals().get(token)]
    if missing_tokens:
        missing_str = ', '.join(missing_tokens)
        logger.critical(f'Отсутствуют следующие токены: {missing_str}')
        raise AbsentEnvironmentVariable(
            f'Отсутствуют следующие токены: {missing_str}'
        )


def send_message(bot, message):
    """Отправка сообщений в Telegram."""
    logger.debug(f'Отправка сообщения: {message}')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение отправлено: {message}')
    except Exception as error:
        logger.error(f'Cбой при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Начало отправки запроса и успешное получение ответа."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise ResponseNot200(
                f'Ошибка {response.status_code} при запросе к {ENDPOINT} '
                f'с параметрами {payload}'
            )
        return response.json()
    except requests.RequestException as error:
        raise Exception(f'Сбой в работе программы: {error}')


def check_response(response):
    """Проверка корректности структуры ответа API."""
    if not isinstance(response, dict):
        raise TypeError(f'response is not a dict, this is {type(response)}')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" отсутствует в ответе')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(f'homeworks is not a list, this is {type(homeworks)}')


def parse_status(homework):
    """Начало исполнения функции и ее завершение."""
    if 'status' not in homework:
        raise KeyError('status not in homework')
    if 'homework_name' not in homework:
        raise KeyError('homework_name not in homework')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Получен недокументированный статус: {status}')
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except AbsentEnvironmentVariable as error:
        logger.critical(error)
        quit()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if not homeworks:
                logger.debug('Список домашних работ пуст')
                continue
            homework = homeworks[0]
            message = parse_status(homework)
            if message != last_error_message:
                send_message(bot, message)
                last_error_message = message
                timestamp = response.get('current_date', timestamp)
            else:
                logger.debug('Повторяющееся сообщение не отправлено.')
        except (requests.exceptions.RequestException,
                TeleBot.apihelper.ApiException) as bot_api_error:
            logger.error(
                f'Ошибка при работе с API Telegram или запросом: '
                f'{bot_api_error}'
            )
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            if error_message != last_error_message:
                send_message(bot, error_message)
                last_error_message = error_message
            logger.exception(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
