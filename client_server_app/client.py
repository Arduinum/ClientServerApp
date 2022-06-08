#!../venv/bin/python3
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime, sleep
from common.utils import send_message, get_message, read_conf
from logging import getLogger
from common.utils import log
# Thread - класс для работы с потоками
from threading import Thread
import logs.client_log_config


name = './common/config.yaml'

client_logger = getLogger('client')


@log
def request_presence(account, conf_name=name):
    """Запрашивает присутствие клиента"""
    client_logger.debug('Выполняется запрос присутствия клиента')
    conf = read_conf(conf_name)
    output = dict()
    output[conf['ACTION']] = conf['PRESENCE']
    output[conf['TIME']] = ctime()
    output[conf['USER_NAME']] = {conf['ACCOUNT_NAME']: account}
    client_logger.debug(f'Запрос присутствия клиента выполнен успешно для пользователя {account}')
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
def create_out_message(account, conf_name=name):
    """Функция возвращает словарь с сообщением о выходе"""
    conf = read_conf(conf_name)
    return {
        conf['ACTION']: conf['OUT'],
        conf['TIME']: ctime(),
        conf['ACCOUNT_NAME']: account
    }


@log
def create_message(serv_sock, account, conf_name=name):
    """Возвращает введённое сообщение"""
    conf = read_conf(conf_name)
    target_user = input('Введите имя пользователя:\n')
    message = input('Введите текст сообщения или команду --> для завершения работы:\n')
    if message == '-->':
        serv_sock.close()
        client_logger.info('Пользователь завершил работу командой')
        print(f'Досвидания {account}!')
        exit(0)
    data_message = {
        conf['ACTION']: conf['MESSAGE'],
        conf['TIME']: ctime(),
        conf['ADDRESSER']: account,
        conf['TARGET']: target_user,
        conf['MESS_TEXT']: message
    }
    client_logger.debug(f'Сформеровано сообщение: {data_message}')
    try:
        send_message(serv_sock, create_message(serv_sock), conf_name)
        client_logger.debug(f'Сообщение для пользователя {target_user} отправлено успешно')
    except Exception as err:
        client_logger.critical(f'{err}, соединение с сервером было потеряно')


def help_for_user():
    """Функция для вывода списка всех возможных команд для пользователя"""
    return 'Список доступных команд:\nsend - написать и отправить сообщение\n' \
           'help - вывести список доступных команд\nexit - завершить работу программы'


@log
def interactive_for_user(sock, user_name, conf_name=name):
    """Функция для интерактивного взаимодействия с пользователем, функции: запрос команд"""
    while True:
        command = input('Ведите команду: ')
        if command == 'help':
            help_str = help_for_user()
            print(help_str)
        elif command == 'send':
            create_message(sock, user_name)
        elif command == 'exit':
            send_message(sock, create_out_message(user_name), conf_name)
            print('Соединение было завершено.')
            client_logger.info('Пользователь завершил работу программы командой.')
            sleep(0.7)
            break
        else:
            print('Команда не найдена! Для вывода списка доступных команд введите - help.')


@log
def message_server_from_user(message, name_client, conf_name=name):
    """Функция - обрабатывает сообщения от других пользователей, которые идут с сервера"""
    conf = read_conf(conf_name)
    while True:
        try:
            if conf['MESS_TEXT'] in message and conf['ADDRESSER'] in message and \
                    message[conf['ACTION']] == conf['MESSAGE'] and conf['ACTION'] in message and \
                    conf['TARGET'] in message and message[conf['TARGET']] == name_client:
                print(f'Получено сообщение от этого пользователя {message[conf["ADDRESSER"]]}:\n'
                      f'{message[conf["MESS_TEXT"]]}')
            else:
                client_logger.error(f'Получено некорректное сообщение сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, JSONDecodeError):
            client_logger.critical('Соединение с сервером было потеряно.')
            break


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
    try:
        if arg_name == 'addr':
            if '-a' in argv:
                return argv[argv.index('-a') + 1]
            elif '--addr' in argv:
                return argv[argv.index('--addr') + 1]
            else:
                for arg in argv:
                    if arg == '-n' or arg == '--name':
                        return None
                return argv[1]
    except IndexError:
        return None
    if arg_name == 'port':
        try:
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
        except IndexError:
            return None
    if arg_name == 'name':
        try:
            if '-n' in argv:
                return argv[argv.index('-n') + 1]
            elif '--name' in argv:
                return argv[argv.index('--name') + 1]
            else:
                if '-a' in argv or '--addr' in argv:
                    return int(argv[3 + 1])
                elif '-a' in argv or '--addr' in argv and '-p' in argv or '--port' in argv:
                    return int(argv[3 + 2])
                else:
                    return argv[3]
        except IndexError:
            return None


@log
def data_connect_serv(conf_name=name):
    """Получает корректные данные для соединения с сервером"""
    client_logger.debug('Получение корректных данных для соединения с сервером')
    conf = read_conf(conf_name)
    addr_server, port_server, name_client = check_argv('addr'), check_argv('port'), check_argv('name')

    if name_client is None:
        while True:
            name_client = input('Введите имя пользователя: ')
            if name_client:
                break
    print(f'Программа клиент. Имя пользователя - {name_client}')

    try:
        if port_server is not None and addr_server is not None:
            if port_server < 1024 or port_server > 65535:
                raise ValueError
            client_logger.info(
                f'Получены корректные адрес сервера {addr_server}, порт сервера {port_server} и имя '
                f'клиента {name_client}')
            return {'addr_server': addr_server, 'port_server': port_server, 'name_client': name_client}

        if port_server is None or addr_server is None:
            client_logger.info(f'Установлены адрес сервера {conf["ADDR_DEF"]}, порт сервера {conf["PORT_DEF"]} '
                               f'по умолчанию так как они не были введены. Имя клиента {name_client}.')
            return {'addr_server': conf['ADDR_DEF'], 'port_server': conf['PORT_DEF'],
                    'name_client': name_client}
    except ValueError:
        client_logger.error('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
        exit(1)
    except KeyError:
        client_logger.error('Неверный ключ словаря для получения данных сервера по умолчанию!')
        exit(1)


def work_client(conf_name=name):
    """Отвечает за запуск и работу клиента"""
    data_connect_server = data_connect_serv(conf_name)
    addr_server, port_server, name_client = data_connect_server['addr_server'], \
        data_connect_server['port_server'], data_connect_server['name_client']
    client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                       f'порт: {port_server}, имя пользователя {name_client}.')
    try:
        server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
        server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
        message_to_serv = request_presence(name_client, conf_name=conf_name)
        client_logger.info(f'Сообщение для сервера сформировано успешно.')
        send_message(server_sock, message_to_serv, conf_name)
        client_logger.info(f'Сообщение для сервера отправлено успешно.')
        answer = get_answer(server_sock)
        client_logger.info(f'Пришёл ответ от сервера - {answer}')
        print('Соединение с сервером установлено.')
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось!')
        exit(1)

    else:
        # старт процесса клиента приёма сообщений
        recipient = Thread(target=message_server_from_user, args=(get_message(server_sock), name_client))
        recipient.daemon = True
        recipient.start()
        client_logger.debug('Старт процесса приёма сообщений.')

        # старт процесса отправки сообщений и интерактивного взаимодействия с пользователем
        interface = Thread(target=interactive_for_user)
        interface.daemon = True
        interface.start()
        client_logger.debug('Старт процесса отправки сообщений и интерактивного взаимодействия с пользователем.')

        while True:
            sleep(0.9)
            if recipient.is_alive() and interface.is_alive():
                continue
            break


if __name__ == '__main__':
    work_client()
