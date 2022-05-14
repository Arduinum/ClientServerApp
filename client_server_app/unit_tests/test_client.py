from common.utils import read_conf
from unittest import TestCase
from client import request_presence, response_analysis, get_answer, data_connect_serv, work_client
from json import dumps
from time import ctime


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


class TestClient(TestCase):
    """Тестовый класс для тестирования функций клиента"""
    name_conf = '../common/config.yaml'
    config = read_conf('../common/config.yaml')
    test_dict_get_ok = {
        config['RESPONSE']: 200
    }
    test_dict_send = {
        config['ACTION']: config['PRESENCE'],
        config['TIME']: ctime(),
        config['USER_NAME']: {
            config['ACCOUNT_NAME']: 'Test_name'
        }
    }
    test_dict_data_connect = {
        config['ADDR_SERV']: config['ADDR_DEF'],
        config['PORT_SERV']: config['PORT_DEF']
    }

    def test_request_presence_name(self):
        """Тестирует правильное ли по умолчанию название аккаунта вернёт функция request_presence()"""
        request_pres = request_presence(conf_name=self.name_conf)
        self.assertEqual(request_pres[self.config['USER_NAME']]['account_name'], 'Guest')

    def test_response_analysis_ok(self):
        """Тестирует функцию response_analysis(), которая анализирует правильный ответ от сервера"""
        self.assertEqual(response_analysis(self.test_dict_get_ok, self.name_conf), '200 : OK')

    def test_get_answer(self):
        # test_sock_ok = TestSocket(self.test_dict_get_ok)
        # print(get_answer(test_sock_ok))
        pass

    def test_data_connect_serv(self):
        """Тестирует данные для подключения на корректность"""
        self.assertEqual(data_connect_serv(self.name_conf), self.test_dict_data_connect)

    def test_work_client(self):
        pass
