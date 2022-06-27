from logging import getLogger
import logs.server_log_config
from sys import exit
from common.utils import read_conf


server_logger = getLogger('server')
conf_name = './common/config.yaml'
conf = read_conf(conf_name)


class PortDescriptor:
    def __set__(self, instance, value):
        server_logger.debug('Получение порта для прослушивания сервером')
        if value < 0:
            server_logger.critical('Номер порта должен быть положительным числом!')
            exit(1)
        if value < 1024 or value > 65535:
            server_logger.critical('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
            exit(1)
        instance.__dict__[self.port] = value
        if self.port == conf['PORT_DEF']:
            server_logger.info(f'Для прослушивания сервером задан порт по умолчанию - {value}')
        else:
            server_logger.info(f'Получен порт для прослушивания сервером - {value}')

    def __set_name__(self, owner, port):
        self.port = port
