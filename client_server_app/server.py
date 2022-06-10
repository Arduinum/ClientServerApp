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
def message_handler(message, mess_list, client, clients, names, conf_name=name):
    """Обрабатывает сообщения от клиентов"""
    server_logger.debug(f'Обработка сообщения от клиента - {message}')
    conf = read_conf(conf_name)
    # если сообщение о присутствии клиента
    if conf['ACTION'] in message and message[conf['ACTION']] == conf['PRESENCE'] and conf['TIME'] in message \
            and conf['USER_NAME'] in message:
        if message[conf['USER_NAME']][conf['ACCOUNT_NAME']] not in names.keys():
            client_now = message[conf['USER_NAME']][conf['ACCOUNT_NAME']]
            names[client_now] = client
            response = {conf['RESPONSE']: 200}
            send_message(client, response, conf_name=conf_name)
            server_logger.debug(f'Присутствие клиента {response} - {client}')
        else:
            response = {
                conf['RESPONSE']: 400,
                conf['ERROR']: 'Такое имя пользователя уже существует!'
            }
            send_message(client, response, conf_name=conf_name)
            clients.remove(client)
            client.close()
            server_logger.debug(f'Имя пользователя {message[conf["USER_NAME"]]} уже существует!')
        return
    # если это сообщение от пользователя
    elif conf['ACTION'] in message and message[conf['ACTION']] == conf['MESSAGE'] and conf['TIME'] in message \
            and conf['MESS_TEXT'] in message and conf['TARGET'] in message and conf['ADDRESSER'] in message:
        mess_list.append(message)
        return
    # если клиент решил выйти
    elif conf['ACTION'] in message and message[conf['ACTION']] == conf['OUT'] and conf['ACCOUNT_NAME'] in message:
        clients.remove(names[message[conf['ACCOUNT_NAME']]])
        names[message[conf['ACCOUNT_NAME']]].close()
        client_now = message[conf['ACCOUNT_NAME']]
        del names[client_now]
    # иначе (если некорректный запрос)
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


@log
def message_for_target(message, names, hear_socks, conf_name=name):
    """Функция отправляющая сообщение определённому пользователю"""
    conf = read_conf(conf_name)

    if message[conf['TARGET']] in names and names[message[conf['TARGET']]] in hear_socks:
        send_message(names[message[conf['TARGET']]], message, conf_name=conf_name)
        server_logger.info(f'Сообщение пользователю {message[conf["TARGET"]]} отправлено успешно.\n'
                           f'Отправитель {message[conf["ADDRESSER"]]}.')
    elif message[conf['TARGET']] in names and names[message[conf['TARGET']]] not in hear_socks:
        raise ConnectionError
    else:
        server_logger.error(f'Пользователь {message[conf["TARGET"]]} должен пройти регистрацию!\n'
                            f'Отправка сообщения доступна лишь зарегестрированным пользователям!')


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
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # устанавливаем опции сокета
    server_sock.settimeout(0.8)  # таймаут для операций с сокетом
    clients_list = list()
    messages_queue = list()
    client_names = dict()  # ключ имя пользователя значение сокет его клиента
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
        # проверка есть ли ждущие клиенты
        try:
            if len(clients_list) > 0:
                r_list, w_list, e_list = select(clients_list, clients_list, [], 0)
        except OSError:
            pass

        # приём сообщений и исключение клиентов с ошибкой
        if len(r_list) > 0:
            for r_client in r_list:
                try:
                    message_handler(get_message(r_client), messages_queue, r_client, clients_list, client_names)
                except (Exception, ):
                    server_logger.info(f'Клиент {r_client.getpeername()} отключился от сервера')
                    clients_list.remove(r_client)

        # обрабратываем сообщения если они есть
        for item in messages_queue:
            try:
                message_for_target(item, client_names, w_list)
            except (Exception, ):
                server_logger.info(f'Соединение с клиентом {item[conf["TARGET"]]} было потеряно')
                clients_list.remove(client_names[item[conf['TARGET']]])
                del client_names[item[conf['TARGET']]]
        messages_queue.clear()


if __name__ == '__main__':
    work_server()
