class ResponseNot200(Exception):
    """Ответ сервера не равен 200."""

    def __init__(self, status_code, *args):
        """Инициализация исключения."""
        self.status_code = status_code
        super().__init__(*args)

    def __str__(self):
        """Текст исключения."""
        return f'Получен некорректный статус код: {self.status_code}'


class AbsentEnvironmentVariable(Exception):
    """Класс исключения для переменных окружения."""

    def __init__(self, *args):
        """Инициализация исключения."""
        super().__init__(*args)

    def __str__(self):
        """Текст исключения."""
        return 'Отсутствует обязательная переменная окружения: ' + ', '.join(
            self.args
        )
