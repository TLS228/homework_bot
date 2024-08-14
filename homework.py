import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import AbsentEnvironmentVariable, ResponseNot200

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)


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
    """Проверяем доступность переменных окружения"""
    if not TELEGRAM_TOKEN:
        raise AbsentEnvironmentVariable('TELEGRAM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        raise AbsentEnvironmentVariable('TELEGRAM_CHAT_ID')
    if not PRACTICUM_TOKEN:
        raise AbsentEnvironmentVariable('PRACTICUM_TOKEN')


def send_message(bot, message):
    """Отправка сообщений в Telegram"""
    logger.debug(f'Отправка сообщения: {message}')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение отправлено: {message}')
    except Exception as error:
        logger.error(f'Cбой при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Получение данных из Yandex.Practicum"""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=payload)
    except requests.RequestException as error:
        logger.error(f'Сбой в работе программы {error}')
    if response.status_code != HTTPStatus.OK:
        raise ResponseNot200
    return response.json()


def check_response(response):
    """Проверяет ответ API.Yandex.Practicum"""
    if not isinstance(response, dict):
        raise TypeError(f'responce is not a dict, this is {type(response)}')
    if 'homeworks' not in response:
        raise KeyError('homeworks not in response')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(f'homeworks is not a list, this is {type(homeworks)}')
    return homeworks


def parse_status(homework):
    """Извлекает информацию из homeworks"""
    if 'status' not in homework:
        raise KeyError('status not in homework')
    if 'homework_name' not in homework:
        raise KeyError('homework_name not in homework')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('status not in HOMEWORK_VERDICTS')
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота"""
    try:
        check_tokens()
    except AbsentEnvironmentVariable as error:
        logger.critical(error)
        quit()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    errors = True
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                homework = homework[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.debug('Список домашних работ пуст')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if errors:
                errors = False
                send_message(bot, message)
            logger.critical(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()