#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from select import select
from common.utils import get_message, send_message, read_conf
from json import JSONDecodeError
from time import ctime
from logging import getLogger
import logs.server_log_config
from common.utils import log

name = './common/config.yaml'

server_logger = getLogger('server')


@log
def message_handler(message, mess_list, client, conf_name=name):
    """Обрабатывает сообщения от клиентов"""
    print(message)
    server_logger.debug(f'Обработка сообщения от клиента - {message}')
    conf = read_conf(conf_name)
    if conf['ACTION'] in message and message[conf['ACTION']] == conf['PRESENCE'] and conf['TIME'] in message \
            and conf['USER_NAME'] in message and message[conf['USER_NAME']][conf['ACCOUNT_NAME']] == 'Guest':
        form_message = {conf['RESPONSE']: 200}
        send_message(client, form_message)
        return
    elif conf['ACTION'] in message and message[conf['ACTION']] == conf['MESSAGE'] and conf['TIME'] in message \
            and conf['MESS_TEXT'] in message:
        mess_list.append((message[conf['ACCOUNT_NAME']], message[conf['MESS_TEXT']]))
        return
    else:
        form_message = {
            conf['RESPONSE']: 400,
            conf['ERROR']: 'Bad Request'
        }
        send_message(client, form_message)
        return


@log
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


@log
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
    addr_listen = get_address(conf_name)
    port_listen = get_port(conf_name)

    if len(addr_listen) == 0:
        server_logger.info(f'Старт сервера на адресе 0.0.0.0:{port_listen}, использующимся для подключения.')
    else:
        server_logger.info(f'Старт сервера на адресе {addr_listen}:{port_listen}, использующимся для подключения.')

    conf = read_conf(conf_name)
    server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
    server_sock.bind((addr_listen, port_listen))  # присваиваем порт и адрес
    server_sock.settimeout(0.8)  # таймаут для операций с сокетом
    clients_list = []
    messages_queue = []
    server_sock.listen(conf['MAX_CONNECT'])  # слушаем порт

    while True:
        try:
            client, client_addr = server_sock.accept()
        except OSError:  # произойдёт если таймаут вышел
            date_now = ctime()
            print(f'{date_now} - timeout is over')
        else:
            server_logger.info(f'Пришёл запрос от клиента на соединение {client_addr}')
            clients_list.append(client)  # добавляем постучавшегося клиента

        r_list, w_list = [], []
        try:
            if len(clients_list) > 0:
                r_list, w_list, e_list = select(clients_list, clients_list, [], 0)
        except OSError:
            pass

        # приём сообщений и исключение клиентов с ошибкой
        if len(r_list) > 0:
            for r_client in r_list:
                try:
                    print(r_client)
                    message_handler(get_message(r_client), messages_queue, r_client)
                except (Exception, ):
                    server_logger.info(f'Клиент {r_client.getpeername()} отключился от сервера')
                    clients_list.remove(r_client)

        # отправка сообщений ожидающим клиентам
        if len(messages_queue) > 0 and len(w_list) > 0:
            server_logger.debug('отправка сообщений ожидающим клиентам')
            data_message = {
                conf['ACTION']: conf['MESSAGE'],
                conf['ADDRESSER']: messages_queue[0][0],
                conf['TIME']: ctime(),
                conf['MESS_TEXT']: messages_queue[0][1]
            }
            messages_queue.pop(0)
            for wait_client in w_list:
                try:
                    server_logger.debug(f'отправка сообщения ожидающиму клиенту {wait_client}')
                    send_message(wait_client, data_message, conf_name)
                except (Exception, ):
                    server_logger.info(f'Клиент {wait_client.getpeername()} отключился от сервера')
                    wait_client.close()
                    clients_list.remove(wait_client)


if __name__ == '__main__':
    work_server()
