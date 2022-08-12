from logging import getLogger
from logs import server_log_config, client_log_config
from sys import exit
from common.utils import read_conf
from common.config_path_file import CONFIG_PATH


class PortDescriptor:
    """Класс для проверки порта"""
    def __init__(self, name_logger):
        self.conf = read_conf(CONFIG_PATH)
        self.name_logger = name_logger

        if self.name_logger == 'server':
            self.logger = getLogger('server')
        elif name_logger == 'client':
            self.logger = getLogger('client')

    def __set__(self, instance, value):
        if self.name_logger == 'server':
            self.name_logger = 'сервер'
        elif self.name_logger == 'client':
            self.name_logger = 'клиент'

        self.logger.debug(f'Получение порта для {self.name_logger}а.')
        if value < 0:
            self.logger.critical('Номер порта должен быть положительным числом!')
            exit(1)
        if value < 1024 or value > 65535:
            self.logger.critical('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
            exit(1)
        instance.__dict__[self.port] = value
        if self.port == self.conf['PORT_DEF']:
            self.logger.info(f'Для работы {self.name_logger}а задан порт по умолчанию - {value}')
        else:
            self.logger.info(f'Получен порт для работы {self.name_logger}а - {value}')

    def __set_name__(self, owner, port):
        self.port = port
