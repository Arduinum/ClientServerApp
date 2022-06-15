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


class Client:
    def __init__(self):
        self.conf_name = './common/config.yaml'
        self.conf = read_conf(self.conf_name)
        self.client_logger = getLogger('client')

    @log
    def request_presence(self, account):
        """Запрашивает присутствие клиента"""
        self.client_logger.debug('Выполняется запрос присутствия клиента')
        output = dict()
        output[self.conf['ACTION']] = self.conf['PRESENCE']
        output[self.conf['TIME']] = ctime()
        output[self.conf['USER_NAME']] = {self.conf['ACCOUNT_NAME']: account}
        self.client_logger.debug(f'Запрос присутствия клиента выполнен успешно для пользователя {account}')
        return output

    @log
    def response_analysis(self, message):
        """Выполняет разбор ответа сервера"""
        self.client_logger.debug(f'Выполняется разбор ответа сервера - {message}')
        for key in message.keys():
            if key == self.conf['RESPONSE']:
                if message[self.conf['RESPONSE']] == 200:
                    self.client_logger.info('Получен ответ от сервера - 200 : OK')
                    return '200 : OK'
                self.client_logger.error(f'Получен ответ с ошибкой от сервера - 400 : {message[self.conf["ERROR"]]}')
                return f'400 : {message[self.conf["ERROR"]]}'
        self.client_logger.critical('Ошибка данных ValueError')
        raise ValueError

    @log
    def create_out_message(self, account):
        """Функция возвращает словарь с сообщением о выходе"""
        return {
            self.conf['ACTION']: self.conf['OUT'],
            self.conf['TIME']: ctime(),
            self.conf['ACCOUNT_NAME']: account
        }

    @log
    def create_message(self, serv_sock, account):
        """Возвращает введённое сообщение"""
        target_user = input('Введите имя пользователя:\n')
        message = input('Введите текст сообщения или команду --> для завершения работы:\n')
        if message == '-->':
            serv_sock.close()
            self.client_logger.info('Пользователь завершил работу командой')
            print(f'Досвидания {account}!')
            exit(0)
        data_message = {
            self.conf['ACTION']: self.conf['MESSAGE'],
            self.conf['TIME']: ctime(),
            self.conf['ADDRESSER']: account,
            self.conf['TARGET']: target_user,
            self.conf['MESS_TEXT']: message
        }
        self.client_logger.debug(f'Сформеровано сообщение: {data_message}')
        try:
            send_message(serv_sock, data_message, self.conf_name)
            self.client_logger.debug(f'Сообщение для пользователя {target_user} отправлено успешно')
        except Exception as err:
            self.client_logger.critical(f'{err}, соединение с сервером было потеряно')

    def help_for_user(self):
        """Функция для вывода списка всех возможных команд для пользователя"""
        return 'Список доступных команд:\nsend - написать и отправить сообщение\n' \
               'help - вывести список доступных команд\nexit - завершить работу программы'

    @log
    def interactive_for_user(self, sock, user_name):
        """Функция для интерактивного взаимодействия с пользователем, функции: запрос команд"""
        while True:
            command = input('Ведите команду: ')
            if command == 'help':
                help_str = self.help_for_user()
                print(help_str)
            elif command == 'send':
                self.create_message(sock, user_name)
            elif command == 'exit':
                send_message(sock, self.create_out_message(user_name), self.conf_name)
                print('Соединение было завершено.')
                self.client_logger.info('Пользователь завершил работу программы командой.')
                sleep(0.7)
                break
            else:
                print('Команда не найдена! Для вывода списка доступных команд введите - help.')

    @log
    def message_server_from_user(self, sock, name_client):
        """Функция - обрабатывает сообщения от других пользователей, которые идут с сервера"""
        self.client_logger.debug('Попытка обработки сообщений от других пользователей')
        while True:
            try:
                message = get_message(sock)
                if message:
                    if self.conf['MESS_TEXT'] in message and self.conf['ADDRESSER'] in message and \
                            message[self.conf['ACTION']] == self.conf['MESSAGE'] and self.conf['ACTION'] in message \
                            and self.conf['TARGET'] in message and message[self.conf['TARGET']] == name_client:
                        print(f'Получено сообщение от этого пользователя {message[self.conf["ADDRESSER"]]}:\n'
                              f'{message[self.conf["MESS_TEXT"]]}')
                    else:
                        self.client_logger.error(f'Получено некорректное сообщение сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, JSONDecodeError):
                self.client_logger.critical('Соединение с сервером было потеряно.')
                break

    @log
    def get_answer(self, serv_sock, conf_name=None):
        """Функция для получения ответа от сервера в правильной кодировке"""
        self.client_logger.debug('Попытка получения сообщения из сокета в правильной кодировке')
        try:
            if conf_name is not None:
                message_ok = self.response_analysis(get_message(serv_sock, conf_name=conf_name), conf_name=conf_name)
                self.client_logger.info(f'Сообщение в правильной кодировке получено - {message_ok}')
                return message_ok
            message_ok = self.response_analysis(get_message(serv_sock))
            self.client_logger.info(f'Сообщение в правильной кодировке получено - {message_ok}')
            return message_ok
        except (ValueError, JSONDecodeError):
            self.client_logger.error('Провал декодирования сообщения сервера!')
            return 'Провал декодирования сообщения сервера!'

    @log
    def check_argv(self, arg_name):
        """Проверяет с префиксами вводят аргумент команды или без префикса и возращает аргумент команды"""
        self.client_logger.debug('Проверка аргументов')
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
    def data_connect_serv(self):
        """Получает корректные данные для соединения с сервером"""
        self.client_logger.debug('Получение корректных данных для соединения с сервером')
        addr_server, port_server, name_client = self.check_argv('addr'), self.check_argv('port'), \
            self.check_argv('name')

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
                self.client_logger.info(
                    f'Получены корректные адрес сервера {addr_server}, порт сервера {port_server} и имя '
                    f'клиента {name_client}')
                return {'addr_server': addr_server, 'port_server': port_server, 'name_client': name_client}

            if port_server is None or addr_server is None:
                self.client_logger.info(f'Установлены адрес сервера {self.conf["ADDR_DEF"]}, порт сервера '
                                        f'{self.conf["PORT_DEF"]} по умолчанию так как они не были введены. '
                                        f'Имя клиента {name_client}.')
                return {'addr_server': self.conf['ADDR_DEF'], 'port_server': self.conf['PORT_DEF'],
                        'name_client': name_client}
        except ValueError:
            self.client_logger.error('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
            exit(1)
        except KeyError:
            self.client_logger.error('Неверный ключ словаря для получения данных сервера по умолчанию!')
            exit(1)

    def work_client(self):
        """Отвечает за запуск и работу клиента"""
        data_connect_server = self.data_connect_serv()
        addr_server, port_server, name_client = data_connect_server['addr_server'], \
            data_connect_server['port_server'], data_connect_server['name_client']
        self.client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                                f'порт: {port_server}, имя пользователя {name_client}.')
        try:
            server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
            server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
            message_to_serv = self.request_presence(name_client, conf_name=self.conf_name)
            self.client_logger.info(f'Сообщение для сервера сформировано успешно.')
            send_message(server_sock, message_to_serv, self.conf_name)
            self.client_logger.info(f'Сообщение для сервера отправлено успешно.')
            answer = self.get_answer(server_sock)
            self.client_logger.info(f'Пришёл ответ от сервера - {answer}')
            print('Соединение с сервером установлено.')
        except (ConnectionRefusedError, ConnectionError):
            self.client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось!')
            exit(1)

        else:
            # старт процесса клиента приёма сообщений
            recipient = Thread(target=self.message_server_from_user, args=(server_sock, name_client))
            recipient.daemon = True
            recipient.start()
            self.client_logger.debug('Старт процесса приёма сообщений.')

            # старт процесса отправки сообщений и интерактивного взаимодействия с пользователем
            interface = Thread(target=self.interactive_for_user, args=(server_sock, name_client))
            interface.daemon = True
            interface.start()
            self.client_logger.debug('Старт процесса отправки сообщений и интерактивного взаимодействия с '
                                     'пользователем.')

            while True:
                sleep(0.9)
                if recipient.is_alive() and interface.is_alive():
                    continue
                break


client = Client()
client.work_client()

if __name__ == '__main__':
    client = Client()
    client.work_client()
