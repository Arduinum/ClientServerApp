from common.utils import read_conf
from unittest import TestCase, main
from client import request_presence, response_analysis, get_answer, data_connect_serv
from time import ctime
from test_utils import TestSocket
from common.config_path_file import CONFIG_PATH


class TestClient(TestCase):
    """Тестовый класс для тестирования функций клиента"""
    config = read_conf(CONFIG_PATH)
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
        request_pres = request_presence(conf_name=CONFIG_PATH)
        self.assertEqual(request_pres[self.config['USER_NAME']]['account_name'], 'Guest')

    def test_response_analysis_ok(self):
        """Тестирует функцию response_analysis(), которая анализирует правильный ответ от сервера"""
        self.assertEqual(response_analysis(self.test_dict_get_ok, CONFIG_PATH), '200 : OK')

    def test_get_answer_ok(self):
        """Тестирует функцию ответа сервера в нужной кодировке"""
        test_sock_ok = TestSocket(self.test_dict_get_ok)
        self.assertEqual(get_answer(test_sock_ok, CONFIG_PATH), '200 : OK')

    def test_data_connect_serv_ok(self):
        """Тестирует данные для подключения на корректность"""
        self.assertEqual(data_connect_serv(CONFIG_PATH), self.test_dict_data_connect)


if __name__ == '__main__':
    main()
