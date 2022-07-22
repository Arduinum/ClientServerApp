from json import JSONDecodeError
from socket import socket, AF_INET, SOCK_STREAM
from sys import path
from time import ctime, sleep
from common.utils import log_client, read_conf, send_message, get_message
path.append('../')
from threading import Thread, Lock
from logging import getLogger
from PyQt5.QtCore import QObject, pyqtSignal
from server import ServerError
from common.config_path_file import CONFIG_PATH

client_logger = getLogger('client')
sock_lock = Lock()
conf = read_conf(CONFIG_PATH)


class ClientTransport(Thread, QObject):
    """Класс для взаимодействия клиента с сервером"""
    # cигналы: новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connect_lost = pyqtSignal()

    def __init__(self, port_server, addr_server, data_base, name_client):
        Thread.__init__(self)
        QObject.__init__(self)
        self.data_base = data_base
        self.name_client = name_client
        self.transport = None  # сокет для работы с серваком
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

    @log_client
    def create_welcome_message(self):
        """Метод класса вернёт приветственное сообщение"""
        return {
            conf['ACTION']: conf['PRESENCE'],
            conf['TIME']: ctime(),
            conf['USER_NAME']: {
                conf['ACCOUNT_NAME']: self.name_client
            }
        }

    @log_client
    def create_out_message(self):
        """Метод класса возвращает словарь с сообщением о выходе"""
        return {
            conf['ACTION']: conf['OUT'],
            conf['TIME']: ctime(),
            conf['ACCOUNT_NAME']: self.name_client
        }

    @log_client
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
            else:
                client_logger.debug(f'Получен не известный код {message[conf["RESPONSE"]]}!')
        # если это сообщение от пользователя добавляем в базу и дадим сигнал о новом сообщении
        elif conf['ACTION'] in message and message[conf['ACTION']] == conf['MESSAGE'] and conf['ADDRESSER'] in message \
                and conf['TARGET'] in message and conf['MESS_TEXT'] in message \
                and message[conf['TARGET']] == self.name_client:
            client_logger.debug(f'Получено сообщение от пользователя {message[conf["ADDRESSER"]]}:'
                                f'{message[conf["MESS_TEXT"]]}')
            self.data_base.save_message(message[conf["ADDRESSER"]], 'in', message[conf['MESS_TEXT']])
            self.new_message.emit(message[conf["ADDRESSER"]])

    @log_client
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
                break
            sleep(1.2)

        if not connect_flag:
            client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось!')
            raise ServerError(f'Подключение к серверу {addr_server}:{port_server} не удалось!')

        client_logger.debug(f'Установлено соединение с сервером {addr_server}:{port_server}')

        try:
            with sock_lock:
                send_message(self.transport, self.create_welcome_message())
                self.response_analysis(get_message(self.transport))
        except (OSError, JSONDecodeError):
            client_logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        client_logger.info('Соединение с сервером установлено.')

    @log_client
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

    @log_client
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

    @log_client
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
            answer = get_message(self.transport)
            if conf['RESPONSE'] in answer and answer[conf['RESPONSE']] == 200:
                pass
            else:
                raise ServerError('Ошибка создания контакта')

    @log_client
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

    @log_client
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

    @log_client
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

    def run(self):
        client_logger.debug('Приёмник сообщений с сервера запущен.')
        while self.running_flag:
            sleep(1.2)
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
                # Если получиили сообщение, то вызываем обработчик:
                else:
                    client_logger.debug(f'Принято сообщение с сервера: {message}')
                    self.response_analysis(message)
                finally:
                    self.transport.settimeout(6)
