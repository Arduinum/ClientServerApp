from server import message_handler, get_address, get_port
from common.utils import read_conf
from unittest import TestCase, main
from time import ctime
from sys import argv
from common.config_path_file import CONFIG_PATH


class TestServer(TestCase):
    """Тестовый класс для тестирования функций сервера"""
    config = read_conf(CONFIG_PATH)
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
        self.assertEqual(message_handler(self.test_dict_get_err, CONFIG_PATH), self.test_dict_get_err)

    def test_get_address_ok(self):
        """Тестирует правильный ли адрес вернёт функция get_address()"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('server.py')
        argv.append('-a')
        argv.append(self.config['ADDR_DEF'])
        self.assertEqual(get_address(CONFIG_PATH), self.config['ADDR_DEF'])

    def test_get_address_none_port(self):
        """Тестирует вернётся ли None если не указать порт в аргументах"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('server.py')
        argv.append('-a')
        self.assertIsNone(get_address(CONFIG_PATH), None)

    def test_get_port_type(self):
        """Тестирует правильный ли тип данных вернёт функция get_port()"""
        argv.clear()
        argv.append('/snap/pycharm-community/276/plugins/python-ce/helpers/pycharm/_jb_unittest_runner.py')
        argv.append('-p')
        argv.append('7778')
        self.assertIsInstance(get_port(CONFIG_PATH), int)


if __name__ == '__main__':
    main()
