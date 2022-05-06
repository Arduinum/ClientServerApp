#!../venv/bin/python3
from os import getenv
from sys import argv, exit
from dotenv import load_dotenv
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.utils import get_message, send_message
from json import JSONDecodeError


load_dotenv(dotenv_path='./common/.env')


def message_handler(message):
    """Обрабатывает сообщения от клиентов"""
    if getenv('ACTION') in message and message[getenv('ACTION')] == getenv('PRESENCE') and getenv('TIME') in message \
            and getenv('USER_NAME') in message and message[getenv('USER_NAME')][getenv('ACCOUNT_NAME')] == 'Guest':
        return {getenv('RESPONSE'): 200}
    return {
        getenv('RESPONSE'): 400,
        getenv('ERROR'): 'Bad Request'
    }


def get_address():
    """Возращает адрес для прослушивания сервером"""
    try:
        for i, addr in enumerate(argv):
            if addr == '-a':
                return argv[i + 1]
        return getenv('ADDR_LISTEN_DEF')
    except IndexError:
        print('После параметра "-a" нужно указать адрес для прослушивания сервером!')


def get_port():
    """Возращает корректный порт для прослушивания сервером"""
    try:
        for i, port in enumerate(argv):
            if port == '-p':
                if int(argv[i + 1]) < 1024 or int(argv[i + 1]) > 65535:
                    raise ValueError
                return int(argv[i + 1])
        return int(getenv('PORT_DEF'))
    except IndexError:
        print('После параметра "-p" нужно указать номер порта!')
        exit(1)
    except ValueError:
        print('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_server():
    """Отвечает за запуск и работу сервера"""
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # задаём опции для сокета
    addr_listen = get_address()
    port_listen = get_port()
    server_sock.bind((addr_listen, port_listen))  # присваиваем порт и адрес
    server_sock.listen(int(getenv('MAX_CONNECT')))  # слушаем порт

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
