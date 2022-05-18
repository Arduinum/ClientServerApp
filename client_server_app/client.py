#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime
from common.utils import send_message, get_message, read_conf
from logging import getLogger
import logs.client_log_config

name = './common/config.yaml'

client_logger = getLogger('client')


def request_presence(account='Guest', conf_name=name):
    """Запрашивает присутствие клиента"""
    client_logger.debug('Выполняется запрос присутствия клиента')
    conf = read_conf(conf_name)
    output = dict()
    output[conf['ACTION']] = conf['PRESENCE']
    output[conf['TIME']] = ctime()
    output[conf['USER_NAME']] = {conf['ACCOUNT_NAME']: account}
    return output


def response_analysis(message, conf_name=name):
    """Выполняет разбор ответа сервера"""
    client_logger.debug(f'Выполняется разбор ответа сервера - {message}')
    conf = read_conf(conf_name)
    for key in message.keys():
        if key == conf['RESPONSE']:
            if message[conf['RESPONSE']] == 200:
                client_logger.info('Получен ответ от сервера - 200 : OK')
                return '200 : OK'
            client_logger.error(f'Получен ответ с ошибкой от сервера - 400 : {message[conf["ERROR"]]}')
            return f'400 : {message[conf["ERROR"]]}'
    client_logger.critical('Ошибка данных ValueError')
    raise ValueError


def get_answer(serv_sock, conf_name=None):
    """Функция для получения ответа от сервера в правильной кодировке"""
    client_logger.debug('Попытка получения сообщения из сокета в правильной кодировке')
    try:
        if conf_name is not None:
            message_ok = response_analysis(get_message(serv_sock, conf_name=conf_name), conf_name=conf_name)
            client_logger.info(f'Сообщение в правильной кодировке получено - {message_ok}')
            return message_ok
        message_ok = response_analysis(get_message(serv_sock))
        client_logger.info(f'Сообщение в правильной кодировке получено - {message_ok}')
        return message_ok
    except (ValueError, JSONDecodeError):
        client_logger.error('Провал декодирования сообщения сервера!')
        return 'Провал декодирования сообщения сервера!'


def data_connect_serv(conf_name=name):
    """Получает корректные данные для соединения с сервером"""
    client_logger.debug('Получение корректных данных дял соединения с сервером')
    conf = read_conf(conf_name)
    try:
        addr_server = argv[1]
        port_server = int(argv[2])
        if port_server < 1024 or port_server > 65535:
            raise ValueError
        client_logger.info(f'Получены корректные адрес сервера {addr_server} и порт сервера {port_server}')
        return {'addr_server': addr_server, 'port_server': port_server}
    except IndexError:
        client_logger.info(f'Установлены адрес сервера {conf["ADDR_DEF"]} и порт сервера {conf["PORT_DEF"]} по умолчанию так '
                    f'как они не были введены')
        return {'addr_server': conf['ADDR_DEF'], 'port_server': conf['PORT_DEF']}
    except ValueError:
        client_logger.error('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_client(conf_name=name):
    """Отвечает за запуск и работу клиента"""
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    data_connect_server = data_connect_serv(conf_name)
    server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
    message_to_serv = request_presence(conf_name=conf_name)
    client_logger.info(f'Сообщение для сервера сформировано успешно')
    send_message(server_sock, message_to_serv, conf_name)
    client_logger.info(f'Сообщение для сервера отправлено успешно')
    answer = get_answer(server_sock)
    client_logger.info(f'Пришёл ответ от сервера - {answer}')
    print(answer)


if __name__ == '__main__':
    work_client()
