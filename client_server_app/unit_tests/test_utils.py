from unittest import TestCase, main
from common.utils import read_conf, get_message, send_message
from json import dumps
from time import ctime
from common.config_path_file import CONFIG_PATH


class TestSocket:
    """Тестовый класс для тестирования отправки и получения сообщений"""
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encode_message = None
        self.get_message = None
        self.config = read_conf(CONFIG_PATH)

    def send(self, message):
        """Отправляет корректно закодированное сообщение"""
        test_message = dumps(self.test_dict)  # превращаем словарь в строку
        self.encode_message = test_message.encode(self.config['ENCODING'])  # кодируем данные
        self.get_message = message

    def recv(self, max_length):
        """Получает данные из сокета"""
        test_message = dumps(self.test_dict)
        return test_message.encode(self.config['ENCODING'])


class TestUtils(TestCase):
    """Тестовый класс для тестирования функций: read_conf(), которая читает файл config.yaml.,
    send_message(), которая кодирует и отправляет сообщение, get_message(), которая получает и декодирует сообщение"""

    config = read_conf(CONFIG_PATH)
    test_dict_get_ok = {
        config['RESPONSE']: 200
    }
    test_dict_get_err = {
        config['RESPONSE']: 400,
        config['ERROR']: 'Bad request!'
    }
    test_dict_send = {
        config['ACTION']: config['PRESENCE'],
        config['TIME']: ctime(),
        config['USER_NAME']: {
            config['ACCOUNT_NAME']: 'Test_name'
        }
    }
    conf_dict = {
        'ADDR_LISTEN_DEF': '',
        'ADDR_SERV': 'addr_server',
        'ADDR_DEF': '127.0.0.1',
        'PORT_DEF': 7777,
        'PORT_SERV': 'port_server',
        'MAX_CONNECT': 6,
        'MAX_MESSAGE_LEN_BYTE': 1024,
        'ENCODING': 'utf-8',
        'ACTION': 'action',
        'TIME': 'time',
        'USER_NAME': 'user',
        'ACCOUNT_NAME': 'account_name',
        'PRESENCE': 'presence',
        'RESPONSE': 'response',
        'ERROR': 'error'
    }

    def test_read_conf(self):
        """Тестирует возращает ли данные функция read_conf()"""
        self.assertTrue(self.config)

    def test_read_conf_2(self):
        """Проверяет правильные ли данные возращает функция read_conf()"""
        self.assertEqual(self.config, self.conf_dict)

    def test_send_message_true(self):
        """Тестирует корректность отправки сообщения"""
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send, CONFIG_PATH)
        self.assertEqual(test_socket.encode_message, test_socket.get_message)

    def test_send_message_error(self):
        """Тестирует сообщение с неправильным типом данных"""
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send, CONFIG_PATH)
        self.assertRaises(TypeError, test_socket.test_dict, test_socket.get_message, 'error_dictionary!')

    def test_send_message_bytes(self):
        """Проверяет имеет ли сообщение тип данных bytes"""
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send, CONFIG_PATH)
        self.assertIsInstance(test_socket.encode_message, bytes)

    def test_get_message_ok(self):
        """Тест приёма сообщения (словаря) на корректность содержимого"""
        test_sock_ok = TestSocket(self.test_dict_get_ok)
        self.assertEqual(get_message(test_sock_ok, CONFIG_PATH), self.test_dict_get_ok)

    def test_get_message_error(self):
        """Тест приёма сообщения c неправильным словарём"""
        test_sock_err = TestSocket(self.test_dict_get_err)
        self.assertEqual(get_message(test_sock_err, CONFIG_PATH), self.test_dict_get_err)

    def test_get_message_key_resp(self):
        """Проверка на содержание части строки в названии ключа словаря из сообщения"""
        test_sock_ok = TestSocket(self.test_dict_get_ok)
        message = get_message(test_sock_ok, CONFIG_PATH)
        key_name = None
        for key in message.keys():
            if 'resp' in key:
                key_name = key
        self.assertIsNotNone(key_name)


if __name__ == '__main__':
    main()
