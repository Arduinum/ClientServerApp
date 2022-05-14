#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime
from common.utils import send_message, get_message, read_conf


name = './common/config.yaml'


def request_presence(account='Guest', conf_name=name):
    """Запрашивает присутствие клиента"""
    conf = read_conf(conf_name)
    output = dict()
    output[conf['ACTION']] = conf['PRESENCE']
    output[conf['TIME']] = ctime()
    output[conf['USER_NAME']] = {conf['ACCOUNT_NAME']: account}
    return output


def response_analysis(message, conf_name=name):
    """Выполняет разбор ответа сервера"""
    conf = read_conf(conf_name)
    for key in message.keys():
        if key == conf['RESPONSE']:
            if message[conf['RESPONSE']] == 200:
                return '200 : OK'
            return f'400 : {message[conf["ERROR"]]}'
    raise ValueError


def get_answer(serv_sock, conf_name=None):
    """Функция для получения ответа от сервера в правильной кодировке"""
    try:
        if conf_name is not None:
            return response_analysis(get_message(serv_sock, conf_name=conf_name), conf_name=conf_name)
        return response_analysis(get_message(serv_sock))
    except (ValueError, JSONDecodeError):
        return 'Провал декодирования сообщения сервера!'


def data_connect_serv(conf_name=name):
    """Получает корректные данные для соединения с сервером"""
    conf = read_conf(conf_name)
    try:
        addr_server = argv[1]
        port_server = int(argv[2])
        if port_server < 1024 or port_server > 65535:
            raise ValueError
        return {'addr_server': addr_server, 'port_server': port_server}
    except IndexError:
        return {'addr_server': conf['ADDR_DEF'], 'port_server': conf['PORT_DEF']}
    except ValueError:
        print('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_client(conf_name=name):
    """Отвечает за запуск и работу клиента"""
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    data_connect_server = data_connect_serv(conf_name)
    server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
    message_to_serv = request_presence(conf_name=conf_name)
    send_message(server_sock, message_to_serv, conf_name)
    answer = get_answer(server_sock)
    print(answer)


if __name__ == '__main__':
    work_client()
