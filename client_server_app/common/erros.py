class ServerError(Exception):
    """Класс ошибка сервера"""
    def __init__(self, text):
        self.text = text
