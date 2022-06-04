#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.utils import get_message, send_message, read_conf
from json import JSONDecodeError
from logging import getLogger
import logs.server_log_config


name = './common/config.yaml'

server_logger = getLogger('server')


def message_handler(message, conf_name=name):
    """Обрабатывает сообщения от клиентов"""
    server_logger.debug(f'Обработка сообщения от клиента - {message}')
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
    server_logger.debug(f'Получение адреса для прослушивания сервером из - {conf_name}')
    conf = read_conf(conf_name)
    try:
        for i, addr in enumerate(argv):
            if addr == '-a':
                server_logger.info(f'Получен адрес для прослушивания сервером - {argv[i + 1]}')
                return argv[i + 1]
        server_logger.info('Для прослушивания сервером задан адрес по умолчанию - 0.0.0.0')
        return conf['ADDR_LISTEN_DEF']
    except IndexError:
        server_logger.critical('После параметра "-a" нужно указать адрес для прослушивания сервером!')


def get_port(conf_name=name):
    """Возращает корректный порт для прослушивания сервером"""
    server_logger.debug(f'Получение порта для прослушивания сервером из - {conf_name}')
    conf = read_conf(conf_name)
    try:
        for i, port in enumerate(argv):
            if port == '-p':
                if int(argv[i + 1]) < 1024 or int(argv[i + 1]) > 65535:
                    raise ValueError
                server_logger.info(f'Получен порт для прослушивания сервером - {argv[i + 1]}')
                return int(argv[i + 1])
        server_logger.info(f'Для прослушивания сервером задан порт по умолчанию - {conf["PORT_DEF"]}')
        return conf['PORT_DEF']
    except IndexError:
        server_logger.critical('После параметра "-p" нужно указать номер порта!')
        exit(1)
    except ValueError:
        server_logger.critical('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)


def work_server(conf_name=name):
    """Отвечает за запуск и работу сервера"""
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
            server_logger.debug(f'Поступило сообщение от клиента - {message_for_client}')
            print(message_for_client)
            response = message_handler(message_for_client)
            server_logger.info(f'Создан ответ для клиента - {response}')
            send_message(client, response)
            server_logger.info('Сообщение клиенту отправлено успешно')
            client.close()
            server_logger.debug('Соединение закрыто')
        except (ValueError, JSONDecodeError):
            server_logger.error('Поступило некорректное сообщение от клиента!')


if __name__ == '__main__':
    work_server()
