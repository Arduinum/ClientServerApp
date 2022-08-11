from json import JSONDecodeError
from os import urandom
from select import select
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from sys import path as sys_path
from time import ctime
sys_path.append('../')
from common.config_path_file import CONFIG_PATH
from threading import Thread
from logging import getLogger
from common.utils import read_conf, get_message, send_message
from common.decorators import log, login_needed
from common.descriptor import PortDescriptor
from binascii import hexlify, a2b_base64
from hmac import new, compare_digest

conf = read_conf(CONFIG_PATH)


class MessageReceiver(Thread):
    """Основной класс сервера для обработки поступающих данных"""
    port_listen = PortDescriptor('server')

    def __init__(self, addr, port, db):
        self.server_logger = getLogger('server')
        self.addr_listen = addr
        self.port_listen = port
        self.db = db
        self.client_names = dict()  # ключ имя пользователя значение сокет его клиента
        self.clients_list = list()
        self.listen_list = None  # прослушиваемые сокеты
        self.error_list = None  # сокеты с ошибками
        self.gui_on = True
        self.run_serv = True
        super().__init__()

    def run(self):
        """Отвечает за запуск и работу основного цикла потока сервера"""
        if len(self.addr_listen) == 0:
            self.server_logger.info(f'Старт сервера на адресе 0.0.0.0:{self.port_listen}, использующимся для '
                                    f'подключения.')
        else:
            self.server_logger.info(
                f'Старт сервера на адресе {self.addr_listen}:{self.port_listen}, использующимся для подключения.')

        server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
        server_sock.bind((self.addr_listen, self.port_listen))  # присваиваем порт и адрес
        server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # устанавливаем опции сокета
        server_sock.settimeout(0.6)  # таймаут для операций с сокетом
        server_sock.listen(conf['MAX_CONNECT'])  # слушаем порт

        while self.run_serv:
            try:
                client, client_addr = server_sock.accept()
            except OSError:  # произойдёт если таймаут вышел
                if not self.gui_on:
                    pass
                else:
                    # date_now = ctime()
                    # print(f'{date_now} - timeout is over')
                    pass
            else:
                self.server_logger.info(f'Пришёл запрос от клиента на соединение {client_addr}')
                client.settimeout(6)
                self.clients_list.append(client)  # добавляем постучавшегося клиента

            receive_list = list()  # список сокетов с данными
            # проверка есть ли ждущие клиенты
            try:
                if len(self.clients_list) > 0:
                    receive_list, self.listen_list, self.error_list = select(
                        self.clients_list, self.clients_list, list(), 0)
            except OSError as err:
                self.server_logger.error(f'{err} - ошибка во время работы с сокетом!')

            # приём сообщений и исключение клиентов с ошибкой
            if len(receive_list) > 0:
                for client_with_mess in receive_list:
                    try:
                        self.message_handler(get_message(client_with_mess), client_with_mess)
                    except (Exception, JSONDecodeError, TypeError) as err:
                        self.server_logger.debug(f'Получина ошибка при работе с клиентом! {err}')
                        self.dell_client(client_with_mess)

    @log
    def user_authorization(self, message, sock_client):
        """Метод класса для авторизации клиента"""
        self.server_logger.debug(f'Обработка сообщения от клиента - {message}')
        # если пользователь не зарегестрирован
        if not self.db.checker_user(message[conf['USER_NAME']][conf['ACCOUNT_NAME']]):
            response = conf['RESP_400']
            response[conf['ERROR']] = 'Пользователь не был зарегистрирован!'
            try:
                self.server_logger.debug(f'Неизвестный пользователь отправил - {response}.')
                send_message(sock_client, response)
            except OSError:
                pass
            self.clients_list.remove(sock_client)
            sock_client.close()
        # если имя пользователя занято
        elif message[conf['USER_NAME']][conf['ACCOUNT_NAME']] in self.client_names.keys():
            response = conf['RESP_400']
            response[conf['ERROR']] = 'Такое имя пользователя уже существует!'
            try:
                self.server_logger.debug(f'Имя пользователя - {message[conf["USER_NAME"]]} занято {response}!')
                send_message(sock_client, response)
            except OSError:
                self.server_logger.debug('OS Error')
                pass
            self.clients_list.remove(sock_client)
            sock_client.close()
        # если пользователь зарегистрирован
        elif self.db.checker_user(message[conf['USER_NAME']][conf['ACCOUNT_NAME']]):
            self.server_logger.debug('Корректное имя пользователя. Старт проверки пароля.')
            auth_mess = conf['RESP_511']
            rand_string = hexlify(urandom(64))  # байты в hex
            auth_mess[conf['DATA']] = rand_string.decode('ascii')  # декодируем байты
            hash_passwd = new(self.db.get_hash(
                message[conf['USER_NAME']][conf['ACCOUNT_NAME']]), rand_string, 'MD5')  # хэш пароля
            digest = hash_passwd.digest()
            self.server_logger.debug(f'Сообщение аутентификации - {auth_mess}')
            try:
                send_message(sock_client, auth_mess)
                answer = get_message(sock_client)
            except OSError as err:
                self.server_logger.debug(f'Ошибка аутентификации - {err}')
                sock_client.close()
                return

            client_digest = a2b_base64(answer[conf['DATA']])

            # если ответ клиента корректный
            if conf['RESPONSE'] in answer and answer[conf['RESPONSE']] == 511 and compare_digest(digest, client_digest):
                self.client_names[message[conf['USER_NAME']][conf['ACCOUNT_NAME']]] = sock_client
                ip, port = sock_client.getpeername()
                try:
                    send_message(sock_client, conf['RESP_200'])
                except OSError:
                    self.dell_client(message[conf['USER_NAME']][conf['ACCOUNT_NAME']])
                self.db.user_login(
                    message[conf['USER_NAME']][conf['ACCOUNT_NAME']], ip, port,
                    message[conf['USER_NAME']][conf['PUB_KEY']])
            else:
                response = conf['RESP_400']
                response[conf['ERROR']] = 'Неверный пароль!'
                try:
                    send_message(sock_client, response)
                except OSError:
                    pass
                self.clients_list.remove(sock_client)
                sock_client.close()

    @log
    def message_for_target(self, message, names, hear_socks):
        """Метод класса отправляющий сообщение определённому пользователю"""
        if message[conf['TARGET']] in names and names[message[conf['TARGET']]] in hear_socks:
            try:
                send_message(names[message[conf['TARGET']]], message)
                self.server_logger.info(f'Сообщение пользователю {message[conf["TARGET"]]} отправлено успешно.\n'
                                        f'Отправитель {message[conf["ADDRESSER"]]}.')
            except OSError:
                self.dell_client(message[conf['TARGET']])
        elif message[conf['TARGET']] in names and names[message[conf['TARGET']]] not in hear_socks:
            self.server_logger.error(
                f'Связь с клиентом {message[conf["TARGET"]]} была потеряна. Соединение сброшено, ошибка отправки.')
            self.dell_client(self.client_names[message[conf["TARGET"]]])
        else:
            self.server_logger.error(f'Пользователь {message[conf["TARGET"]]} должен пройти регистрацию!\n'
                                     f'Отправка сообщения доступна лишь зарегестрированным пользователям!')

    @login_needed
    def message_handler(self, message, client):
        """Обрабатывает сообщения от клиентов"""
        self.server_logger.debug(f'Обработка сообщения от клиента - {message}')
        # если сообщение о присутствии клиента
        if conf['ACTION'] in message and message[conf['ACTION']] == conf['PRESENCE'] and \
                conf['TIME'] in message and conf['USER_NAME'] in message:
            self.user_authorization(message, client)  # авторизовываем клиента
        # если это сообщение от пользователя
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['MESSAGE'] and \
                conf['TIME'] in message and conf['MESS_TEXT'] in message and conf['TARGET'] in message \
                and conf['ADDRESSER'] in message and self.client_names[message[conf['ADDRESSER']]] == client:
            if message[conf['TARGET']] in self.client_names:
                self.db.working_message(message[conf['ADDRESSER']], message[conf['TARGET']])
                self.message_for_target(message, self.client_names, self.listen_list)
                try:
                    send_message(client, conf['RESP_200'])
                except OSError:
                    self.dell_client(client)
            else:
                response = conf['RESP_400']
                response[conf['ERROR']] = 'Пользователь не был зарегистрирован!'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return
        # если клиент решил выйти
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['OUT'] and \
                conf['ACCOUNT_NAME'] in message and self.client_names[message[conf['ACCOUNT_NAME']]] == client:
            self.dell_client(client)
        # если делает запрос контакт
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['GET_CONTACTS'] \
                and conf['USER_NAME'] in message and self.client_names[message[conf['USER_NAME']]] == client:
            response = conf['RESP_202']
            response[conf['DATA_LIST']] = self.db.get_users_contacts(message[conf['USER_NAME']])
            try:
                send_message(client, response)
            except OSError:
                self.dell_client(client)
        # если запрос на добавление контакта
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['ADD_CONTACT'] \
                and conf['ACCOUNT_NAME'] in message and conf['USER_NAME'] in message \
                and self.client_names[message[conf['USER_NAME']]] == client:
            self.db.add_contact(message[conf['USER_NAME']], message[conf['ACCOUNT_NAME']])
            try:
                send_message(client, conf['RESP_200'])
            except OSError:
                self.dell_client(client)
        # если запрос на удаление контакта
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['DEL_CONTACT'] \
                and conf['ACCOUNT_NAME'] in message and conf['USER_NAME'] in message \
                and self.client_names[message[conf['USER_NAME']]] == client:
            self.db.delete_contact(message[conf['USER_NAME']], message[conf['ACCOUNT_NAME']])
            try:
                send_message(client, conf['RESP_200'])
            except OSError:
                self.dell_client(client)
        # если запрос от известного пользователя
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['GET_USERS'] \
                and conf['ACCOUNT_NAME'] in message \
                and self.client_names[message[conf['ACCOUNT_NAME']]] == client:
            response = conf['RESP_202']
            response[conf['DATA_LIST']] = [user[0] for user in self.db.get_list_data('users')]
            try:
                send_message(client, response)
            except OSError:
                self.dell_client(client)
        # если запрос публичного ключа пользователя
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['GET_PUB_KEY'] \
                and conf['ACCOUNT_NAME'] in message:
            response = conf['RESP_511']
            response[conf['DATA']] = self.db.get_pub_key(message[conf['ACCOUNT_NAME']])
            if response[conf['DATA']]:
                try:
                    send_message(client, response)
                except OSError:
                    self.dell_client(client)
            else:
                response = conf['RESP_400']
                response[conf['ERROR']] = 'Для данного пользователя публичный ключ не найден!'
                try:
                    send_message(client, response)
                except OSError:
                    self.dell_client(client)
        # иначе (если некорректный запрос)
        else:
            response = conf['RESP_400']
            response[conf['ERROR']] = 'Bad Request'
            try:
                send_message(client, response)
            except OSError:
                self.dell_client(client)

    @log
    def dell_client(self, client):
        """Метод класса удаляющий из списка и базы клиента с прервавшейся связью"""
        self.server_logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for client_name in self.client_names:
            if self.client_names[client_name] == client:
                self.db.user_logout(client_name)
                del self.client_names[client_name]
                break
        self.clients_list.remove(client)
        client.close()

    @log
    def service_updater_lists(self):
        """Метод класса для отправки сервисного сообщения 205 клиентам"""
        for client in self.client_names:
            try:
                send_message(self.client_names[client], conf['RESP_205'])
            except OSError:
                self.dell_client(self.client_names[client])
