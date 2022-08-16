import hmac
from binascii import hexlify, b2a_base64
from hashlib import pbkdf2_hmac
from json import JSONDecodeError
from socket import socket, AF_INET, SOCK_STREAM
from sys import path
path.append('../')
from time import ctime, sleep
from common.utils import read_conf, send_message, get_message
from common.decorators import log
from threading import Thread, Lock
from logging import getLogger
from PyQt5.QtCore import QObject, pyqtSignal
from common.erros import ServerError
from common.config_path_file import CONFIG_PATH

client_logger = getLogger('client')
sock_lock = Lock()
conf = read_conf(CONFIG_PATH)


class ClientTransport(Thread, QObject):
    """Класс для взаимодействия клиента с сервером"""
    # cигналы: новое сообщение и потеря соединения
    new_message = pyqtSignal(dict)
    connect_lost = pyqtSignal()
    mess_205 = pyqtSignal()

    def __init__(self, port_server, addr_server, data_base, name_client, password, keys_encrypt):
        Thread.__init__(self)
        QObject.__init__(self)
        self.data_base = data_base
        self.name_client = name_client
        self.transport = None  # сокет для работы с серваком
        self.password = password
        self.keys_encrypt = keys_encrypt
        self.connect_init(port_server, addr_server)

        # обновление таблиц известных пользователей и контактов
        try:
            self.user_list_request()
            self.contacts_list_request()
        except OSError as err:
            if err.errno:
                client_logger.critical('Соединение с сервером было потеряно!')
                raise ServerError('Соединение с сервером было потеряно!')
            client_logger.error('Timeout соединения при обновлении списка пользователей!')
        except JSONDecodeError:
            client_logger.critical('Соединение с сервером было потеряно!')
            raise ServerError('Соединение с сервером было потеряно!')
        # флаг для продолжения работы транспорта
        self.running_flag = True

    @log
    def create_welcome_message(self):
        """Метод класса вернёт приветственное сообщение"""
        return {
            conf['ACTION']: conf['PRESENCE'],
            conf['TIME']: ctime(),
            conf['USER_NAME']: {
                conf['ACCOUNT_NAME']: self.name_client,
                conf['PUB_KEY']: None
            }
        }

    @log
    def create_out_message(self):
        """Метод класса возвращает словарь с сообщением о выходе"""
        return {
            conf['ACTION']: conf['OUT'],
            conf['TIME']: ctime(),
            conf['ACCOUNT_NAME']: self.name_client
        }

    @log
    def response_analysis(self, message):
        """Метод класса выполняющий разбор ответа сервера"""
        client_logger.debug(f'Выполняется разбор ответа сервера - {message}')
        if conf['RESPONSE'] in message:
            if message[conf['RESPONSE']] == 200:
                client_logger.info('Получен ответ от сервера - 200 : OK')
                return
            elif message[conf['RESPONSE']] == 400:
                client_logger.error(f'Получен ответ с ошибкой от сервера - 400 : {message[conf["ERROR"]]}')
                raise ServerError(f'{message[conf["ERROR"]]}')
            elif message[conf['RESPONSE']] == 205:
                client_logger.debug('Получен запрос на изменение данных.')
                self.user_list_request()
                self.contacts_list_request()
                self.mess_205.emit()
            else:
                client_logger.debug(f'Получен не известный код {message[conf["RESPONSE"]]}!')
        # если это сообщение от пользователя добавляем в базу и дадим сигнал о новом сообщении
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['MESSAGE'] and conf['ADDRESSER'] in message \
                and conf['TARGET'] in message and conf['MESS_TEXT'] in message \
                and message[conf['TARGET']] == self.name_client:
            client_logger.debug(f'Получено сообщение от пользователя {message[conf["ADDRESSER"]]}:'
                                f'{message[conf["MESS_TEXT"]]}')
            self.new_message.emit(message)

    @log
    def connect_init(self, port_server, addr_server):
        """Метод класса для инициализации соединения с сервером"""
        self.transport = socket(AF_INET, SOCK_STREAM)
        # таймаут для освобождения сокета
        self.transport.settimeout(6)

        # пытаемся соединиться 6 попыток, флаг успеха ставим в True если удалось
        connect_flag = False
        for i in range(6):
            client_logger.info(f'Номер попытки подключения - {i + 1}')
            try:
                self.transport.connect((addr_server, port_server))
            except (OSError, ConnectionRefusedError, ConnectionError):
                pass
            else:
                connect_flag = True
                client_logger.debug(f'Установлено соединение с сервером {addr_server}:{port_server}')
                break
            sleep(1.2)

        if not connect_flag:
            client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось!')
            raise ServerError(f'Подключение к серверу {addr_server}:{port_server} не удалось!')

        client_logger.debug(f'Старт диалога аутентификации.')

        # получение хэша пароля
        password_bytes = self.password.encode('utf-8')
        salt = self.name_client.lower().encode('utf-8')
        password_hash = pbkdf2_hmac('sha512', password_bytes, salt, 10000)
        passwd_hash_string = hexlify(password_hash)

        client_logger.debug(f'Хеш пароля готов: {passwd_hash_string}')

        # получение публичного ключа и декодирование его из байт
        pub_key = self.keys_encrypt.publickey().export_key().decode('ascii')

        # авторизация
        with sock_lock:
            req = self.create_welcome_message()
            req[conf['USER_NAME']][conf['PUB_KEY']] = pub_key
            client_logger.debug(f'Приветственное сообщение - {req}')

            # отправка серверу приветственного сообщения
            try:
                send_message(self.transport, req)
                ans = get_message(self.transport)
                client_logger.debug(f'Ответ сервера - {ans}.')

                if conf['RESPONSE'] in ans:
                    if ans[conf['RESPONSE']] == 400:
                        raise ServerError(ans[conf['ERROR']])
                    elif ans[conf['RESPONSE']] == 511:
                        # если всё впорядке авторизация продолжается
                        answer_data = ans[conf['DATA']]
                        hash_passwd = hmac.new(passwd_hash_string, answer_data.encode('utf-8'), 'MD5')
                        digest = hash_passwd.digest()
                        my_answer = conf['RESP_511']
                        my_answer[conf['DATA']] = b2a_base64(digest).decode('ascii')
                        send_message(self.transport, my_answer)
                        self.response_analysis(get_message(self.transport))
            except (OSError, JSONDecodeError):
                client_logger.critical('Потеряно соединение с сервером!')
                raise ServerError('Потеряно соединение с сервером!')

    @log
    def user_list_request(self):
        """Метод класса делает запрос известных пользователей и обновляет их в бд"""
        client_logger.debug(f'Запрос списка известных пользователей {self.name_client}')
        req = {
            conf['ACTION']: conf['GET_USERS'],
            conf['TIME']: ctime(),
            conf['ACCOUNT_NAME']: self.name_client
        }
        with sock_lock:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        if conf['RESPONSE'] in answer and answer[conf['RESPONSE']] == 202:
            self.data_base.add_users(answer[conf['DATA_LIST']])
        else:
            client_logger.error('Список известных пользователей не был обнавлён!')

    @log
    def contacts_list_request(self):
        """Метод класса для запроса листа контактов и их обновления в бд"""
        client_logger.debug(f'Запрос контакт листа для пользователя {self.name_client}')
        req = {
            conf['ACTION']: conf['GET_CONTACTS'],
            conf['TIME']: ctime(),
            conf['USER_NAME']: self.name_client
        }
        client_logger.debug(f'Сформирован запрос {req}')
        with sock_lock:
            send_message(self.transport, req)
            answer = get_message(self.transport)
            client_logger.debug(f'Получен ответ {answer}')
        if conf['RESPONSE'] in answer and answer[conf['RESPONSE']] == 202:
            for cont in answer[conf['DATA_LIST']]:
                self.data_base.add_contact(cont)
        else:
            client_logger.error('Не удалось обновление списка контактов!')

    @log
    def add_contact(self, contact):
        """Метод класса добавляющий пользователя в список контактов"""
        client_logger.debug(f'Попытка создать контакт - {contact}')
        req = {
            conf['ACTION']: conf['ADD_CONTACT'],
            conf['TIME']: ctime(),
            conf['USER_NAME']: self.name_client,
            conf['ACCOUNT_NAME']: contact
        }
        with sock_lock:
            send_message(self.transport, req)
            self.response_analysis(get_message(self.transport))

    @log
    def dell_contact(self, contact):
        """Метод класса для удаления контакта"""
        client_logger.debug(f'Попытка удаления контакта {contact}.')
        req = {
            conf['ACTION']: conf['DEL_CONTACT'],
            conf['TIME']: ctime(),
            conf['USER_NAME']: self.name_client,
            conf['ACCOUNT_NAME']: contact
        }
        with sock_lock:
            send_message(self.transport, req)
            self.response_analysis(get_message(self.transport))

    @log
    def transport_close(self):
        """Метод класса для завершения работы транспорта"""
        self.running_flag = False
        message = self.create_out_message()
        with sock_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        client_logger.debug('Транспорт выключается.')
        sleep(0.6)

    @log
    def send_message(self, target, message):
        """Метод класса для отправки сообщений"""
        message_dict = {
            conf['ACTION']: conf['MESSAGE'],
            conf['ADDRESSER']: self.name_client,
            conf['TARGET']: target,
            conf['TIME']: ctime(),
            conf['MESS_TEXT']: message
        }
        client_logger.debug(f'Было сформированно сообщение: {message_dict}.')

        with sock_lock:
            send_message(self.transport, message_dict)
            self.response_analysis(get_message(self.transport))
            client_logger.info(f'Сообщение выслано пользователю {target}.')

    @log
    def key_pub_request(self, login):
        """Метод класса для запроса с сервера публичного ключа."""
        client_logger.debug(f'Попытка запроса публичного ключа для - {login}')
        req = {
            conf['ACTION']: conf['GET_PUB_KEY'],
            conf['TIME']: ctime(),
            conf['ACCOUNT_NAME']: login
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if conf['RESPONSE'] in ans and ans[conf['RESPONSE']] == 511:
            return ans[conf['DATA']]
        else:
            client_logger.error(f'Получение ключа собеседника не вышло {login}!')

    @log
    def run(self):
        client_logger.debug('Приёмник сообщений с сервера запущен.')
        while self.running_flag:
            sleep(1.2)
            message = None
            with sock_lock:
                if not self.running_flag:
                    break
                try:
                    self.transport.settimeout(0.6)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        client_logger.critical('Соединение с сервером было потеряно!')
                        self.running_flag = False
                        self.connect_lost.emit()
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, JSONDecodeError, TypeError):
                    client_logger.debug('Соединение с сервером было потеряно!.')
                    self.running_flag = False
                    self.connect_lost.emit()
                finally:
                    self.transport.settimeout(6)

            # Если получиили сообщение, то вызываем обработчик:
            if message:
                client_logger.debug(f'Принято сообщение с сервера: {message}')
                self.response_analysis(message)
