#!../venv/bin/python3
from sys import argv, exit
from os import getenv
from dotenv import load_dotenv
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime
from common.utils import send_message, get_message


load_dotenv(dotenv_path='./common/.env')


def request_presence(account='Guest'):
    """Запрашивает присутствие клиента"""
    output = dict()
    output[getenv('ACTION')] = getenv('PRESENCE')
    output[getenv('TIME')] = ctime()
    output[getenv('USER_NAME')] = {getenv('ACCOUNT_NAME'): account}
    return output


def response_analysis(message):
    """Выполняет разбор ответа сервера"""
    for key in message.keys():
        if key == getenv('RESPONSE'):
            if message[getenv('RESPONSE')] == 200:
                return '200 : OK'
            return f'400 : {message[getenv("ERROR")]}'
    raise ValueError


def get_answer(serv_sock):
    try:
        return response_analysis(get_message(serv_sock))
    except (ValueError, JSONDecodeError):
        return 'Провал декодирования сообщения сервера!'


def data_connect_serv():
    """Получает корректные данные для соединения с сервером"""
    try:
        addr_server = argv[1]
        port_server = int(argv[2])
        if port_server < 1024 or port_server > 65535:
            raise ValueError
        return {'addr_server': addr_server, 'port_server': port_server}
    except IndexError:
        return {'addr_server': getenv('ADDR_DEF'), 'port_server': getenv('PORT_DEF')}
    except ValueError:
        print('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_client():
    """Отвечает за запуск и работу клиента"""
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    data_connect_server = data_connect_serv()
    server_sock.connect((data_connect_server['addr_server'], int(data_connect_server['port_server'])))
    message_to_serv = request_presence()
    send_message(server_sock, message_to_serv)
    answer = get_answer(server_sock)
    print(answer)


if __name__ == '__main__':
    work_client()
