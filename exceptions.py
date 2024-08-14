class AbsentEnvironmentVariable(Exception):
    """Класс исключения для переменных окружения."""

    def __init__(self, *args):
        """Инициализация."""
        self.arg = args[0] if args else None

    def __str__(self):
        """Текст ислючения."""
        return ('Отсутствует обязательная переменная окружения: '
                f'\'{self.arg}\' '
                'Программа принудительно остановлена.')


class ResponseNot200(Exception):
    """Ответ сервера не равен 200."""