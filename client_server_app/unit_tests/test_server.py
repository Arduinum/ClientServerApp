from server import message_handler, get_address, get_port, work_server
from common.utils import read_conf
from unittest import TestCase
from time import ctime
from json import dumps
from sys import argv


class TestSocket:
    """Тестовый класс для тестирования отправки и получения сообщений"""
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encode_message = None
        self.get_message = None
        self.config = read_conf('../common/config.yaml')

    def send(self, message):
        """Отправляет корректно закодированное сообщение"""
        test_message = dumps(self.test_dict)  # превращаем словарь в строку
        self.encode_message = test_message.encode(self.config['ENCODING'])  # кодируем данные
        self.get_message = message

    def recv(self, max_length):
        """Получает данные из сокета"""
        test_message = dumps(self.test_dict)
        return test_message.encode(self.config['ENCODING'])


class TestServer(TestCase):
    """Тестовый класс для тестирования функций сервера"""
    config = read_conf('../common/config.yaml')
    name_conf = '../common/config.yaml'
    test_dict_get_ok = {
        config['RESPONSE']: 200
    }
    test_dict_get_err = {
        config['RESPONSE']: 400,
        config['ERROR']: 'Bad Request'
    }
    test_dict_send = {
        config['ACTION']: config['PRESENCE'],
        config['TIME']: ctime(),
        config['USER_NAME']: {
            config['ACCOUNT_NAME']: 'Test_name'
        }
    }

    def test_message_handler_ok(self):
        """Тестирует если пришёл не правильный словарь в сообщении"""
        self.assertEqual(message_handler(self.test_dict_get_err, self.name_conf), self.test_dict_get_err)

    def test_get_address_ok(self):
        """Тестирует правильный ли адрес вернёт функция get_address()"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('server.py')
        argv.append('-a')
        argv.append(self.config['ADDR_DEF'])
        self.assertEqual(get_address(self.name_conf), self.config['ADDR_DEF'])

    def test_get_address_none_port(self):
        """Тестирует вернётся ли None если не указать порт в аргументах"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('server.py')
        argv.append('-a')
        self.assertIsNone(get_address(self.name_conf), None)

    def test_get_port_type(self):
        """Тестирует правильный ли тип данных вернёт функция get_port()"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('-p')
        argv.append('7778')
        self.assertIsInstance(get_port(self.name_conf), int)

    def test_work_server(self):
        """Тестирует работу сервера"""
        pass
