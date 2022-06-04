#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime
from common.utils import send_message, get_message, read_conf
from logging import getLogger
from common.utils import log
import logs.client_log_config

name = './common/config.yaml'

client_logger = getLogger('client')


class ModeError(Exception):
    def __str__(self):
        return 'Ошибка ModeError'


@log
def request_presence(account='Guest', conf_name=name):
    """Запрашивает присутствие клиента"""
    client_logger.debug('Выполняется запрос присутствия клиента')
    conf = read_conf(conf_name)
    output = dict()
    output[conf['ACTION']] = conf['PRESENCE']
    output[conf['TIME']] = ctime()
    output[conf['USER_NAME']] = {conf['ACCOUNT_NAME']: account}
    return output


@log
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


@log
def create_message(serv_sock, account='Guest', conf_name=name):
    """Возвращает введённое сообщение"""
    conf = read_conf(conf_name)
    message = input('Введите текст сообщения или команду --> для завершения работы:\n')
    if message == '-->':
        serv_sock.close()
        client_logger.info('Пользователь завершил работу командой')
        print(f'Досвидания {account}!')
        exit(0)
    data_message = {
        conf['ACTION']: conf['MESSAGE'],
        conf['TIME']: ctime(),
        conf['ACCOUNT_NAME']: account,
        conf['MESS_TEXT']: message
    }
    client_logger.debug(f'Сформеровано сообщение: {data_message}')
    return data_message


@log
def message_server_from_user(message, conf_name=name):
    """Функция - обрабатывает сообщения от других пользователей, которые идут с сервера"""
    conf = read_conf(conf_name)
    if conf['MESS_TEXT'] in message and conf['ADDRESSER'] in message and message[conf['ACTION']] == conf['MESSAGE'] \
            and conf['ACTION'] in message:
        print(f'Получено сообщение от этого пользователя {message[conf["ADDRESSER"]]}:\n{message[conf["MESS_TEXT"]]}')
    else:
        client_logger.error(f'Получено некорректное сообщение сообщение с сервера: {message}')


@log
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


@log
def check_argv(arg_name):
    """Проверяет с префиксами вводят аргумент команды или без префикса и возращает аргумент команды"""
    client_logger.debug('Проверка аргументов')
    if arg_name == 'addr':
        if '-a' in argv:
            return argv[argv.index('-a') + 1]
        elif '--addr' in argv:
            return argv[argv.index('--addr') + 1]
        else:
            return argv[1]
    if arg_name == 'port':
        if '-p' in argv:
            return argv[argv.index('-p') + 1]
        elif '--port' in argv:
            return argv[argv.index('--port') + 1]
        else:
            if '-a' in argv or '--addr' in argv:
                return int(argv[2 + 1])
            else:
                for port in argv:
                    if port.isdigit():
                        return int(port)
                return None
    if arg_name == 'mode':
        if '-m' in argv:
            return argv[argv.index('-m') + 1]
        elif '--mode' in argv:
            return argv[argv.index('--mode') + 1]
        else:
            if '-a' in argv or '--addr' in argv:
                return int(argv[3 + 1])
            elif '-a' in argv or '--addr' in argv and '-p' in argv or '--port' in argv:
                return int(argv[3 + 2])
            else:
                for mode in argv:
                    if mode == 'send':
                        return argv[argv.index('send')]
                    if mode == 'listen':
                        return argv[argv.index('listen')]
                return None


@log
def data_connect_serv(conf_name=name):
    """Получает корректные данные для соединения с сервером"""
    addr_server, port_server, mode_client = None, None, None
    client_logger.debug('Получение корректных данных для соединения с сервером')
    conf = read_conf(conf_name)
    try:
        if 'listen' not in argv and 'send' not in argv:
            raise ModeError
        addr_server, port_server, mode_client = check_argv('addr'), check_argv('port'), check_argv('mode')

        if port_server is not None:
            if port_server < 1024 or port_server > 65535:
                raise ValueError
            client_logger.info(
                f'Получены корректные адрес сервера {addr_server}, порт сервера {port_server} и мод для '
                f'клиента {mode_client}')
            return {'addr_server': addr_server, 'port_server': port_server, 'mode_client': mode_client}

        if port_server is None or addr_server is None:
            client_logger.info(f'Установлены адрес сервера {conf["ADDR_DEF"]}, порт сервера {conf["PORT_DEF"]} '
                               f'по умолчанию так как они не были введены. Режим для клиента {mode_client}.')
            return {'addr_server': conf['ADDR_DEF'], 'port_server': conf['PORT_DEF'],
                    'mode_client': mode_client}
    except ValueError:
        client_logger.error('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)
    except ModeError as err:
        client_logger.error(f'{err} вы указали неправильный режим работы {mode_client}, вам доступны следующие режимы: '
                            f'listen, send')
        exit(1)


def work_client(conf_name=name):
    """Отвечает за запуск и работу клиента"""
    data_connect_server = data_connect_serv(conf_name)
    addr_server, port_server, mode_client = data_connect_server['addr_server'], \
        data_connect_server['port_server'], data_connect_server['mode_client']
    client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                       f'порт: {port_server}, режим работы {mode_client}')
    try:
        server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
        server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
        message_to_serv = request_presence(conf_name=conf_name)
        client_logger.info(f'Сообщение для сервера сформировано успешно')
        send_message(server_sock, message_to_serv, conf_name)
        client_logger.info(f'Сообщение для сервера отправлено успешно')
        answer = get_answer(server_sock)
        client_logger.info(f'Пришёл ответ от сервера - {answer}')
        print('Соединение с сервером установлено.')
    except ConnectionRefusedError:
        client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось')
        exit(1)
    else:
        if mode_client == 'send':
            print('Режим работы клиента - отправка сообщений')
        if mode_client == 'listen':
            print('Режим работы клиента - приём сообщений')

        while True:
            if mode_client == 'send':
                try:
                    send_message(server_sock, create_message(server_sock), conf_name)
                except (ConnectionRefusedError, ConnectionAbortedError):
                    client_logger.error(f'Соединение с сервером {addr_server}:{port_server} потеряно')
                    exit(1)

            if mode_client == 'listen':
                # клиент выключается, который слушает после отправки сообщения!!!
                try:
                    message_server_from_user(get_message(server_sock))
                except (ConnectionRefusedError, ConnectionAbortedError):
                    client_logger.error(f'Соединение с сервером {addr_server}:{port_server} потеряно')
                    exit(1)


if __name__ == '__main__':
    argv.append('send')
    work_client()
