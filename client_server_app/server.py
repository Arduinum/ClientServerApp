#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.utils import get_message, send_message, read_conf
from json import JSONDecodeError

name = './common/config.yaml'


def message_handler(message, conf_name=name):
    """Обрабатывает сообщения от клиентов"""
    conf = read_conf(conf_name)
    if conf['ACTION'] in message and message[conf['ACTION']] == conf['PRESENCE'] and conf['TIME'] in message \
            and conf['USER_NAME'] in message and message[conf['USER_NAME']][conf['ACCOUNT_NAME']] == 'Guest':
        return {conf['RESPONSE']: 200}
    return {
        conf['RESPONSE']: 400,
        conf['ERROR']: 'Bad Request'
    }


def get_address(conf_name=name):
    """Возращает адрес для прослушивания сервером"""
    conf = read_conf(conf_name)
    try:
        for i, addr in enumerate(argv):
            if addr == '-a':
                return argv[i + 1]
        return conf['ADDR_LISTEN_DEF']
    except IndexError:
        print('После параметра "-a" нужно указать адрес для прослушивания сервером!')


def get_port(conf_name=name):
    """Возращает корректный порт для прослушивания сервером"""
    conf = read_conf(conf_name)
    try:
        for i, port in enumerate(argv):
            if port == '-p':
                if int(argv[i + 1]) < 1024 or int(argv[i + 1]) > 65535:
                    raise ValueError
                return int(argv[i + 1])
        return conf['PORT_DEF']
    except IndexError:
        print('После параметра "-p" нужно указать номер порта!')
        exit(1)
    except ValueError:
        print('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_server(conf_name=name, command=None):
    """Отвечает за запуск и работу сервера"""
    if command == 'test':
        conf_name = '.' + conf_name
    conf = read_conf(conf_name)
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # задаём опции для сокета
    addr_listen = get_address(conf_name)
    port_listen = get_port(conf_name)
    server_sock.bind((addr_listen, port_listen))  # присваиваем порт и адрес
    server_sock.listen(conf['MAX_CONNECT'])  # слушаем порт

    while True:
        client, client_addr = server_sock.accept()
        try:
            message_for_client = get_message(client)
            print(message_for_client)
            response = message_handler(message_for_client)
            send_message(client, response)
            client.close()
        except (ValueError, JSONDecodeError):
            print('Поступило некорректное сообщение от клиента!')


if __name__ == '__main__':
    work_server()
