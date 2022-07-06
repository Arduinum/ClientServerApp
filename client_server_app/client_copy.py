#!../venv/bin/python3
from os.path import dirname, realpath
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from json import JSONDecodeError
from time import ctime, sleep
from common.utils import send_message, get_message, read_conf
from logging import getLogger
from common.utils import log_client
# Thread - класс для работы с потоками
from threading import Thread, Lock
from metaclasses import ClientVerifier
import logs.client_log_config
from server import ServerError
from client_storage import ClientStorage
# Объект для блокировки сокета и работы с базой данных
socket_lock = Lock()
db_lock = Lock()


class Client(Thread):
    """Класс клиент, который запускает две части клиента"""

    def __init__(self):
        super().__init__()
        self.conf_name = './common/config.yaml'
        self.conf = read_conf(self.conf_name)
        self.client_logger = getLogger('client')

    # @log_client
    def request_presence(self, account):
        """Запрашивает присутствие клиента"""
        self.client_logger.debug('Выполняется запрос присутствия клиента')
        output = dict()
        output[self.conf['ACTION']] = self.conf['PRESENCE']
        output[self.conf['TIME']] = ctime()
        output[self.conf['USER_NAME']] = {self.conf['ACCOUNT_NAME']: account}
        self.client_logger.debug(f'Запрос присутствия клиента выполнен успешно для пользователя {account}')
        return output

    # @log_client
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

    # @log_client
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

    # @log_client
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

    # @log_client
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

    # @log_client
    def user_list_request(self, sock, username):
        """Метод класса делает запрос известных пользователей"""
        self.client_logger.debug(f'Запрос списка известных пользователей {username}')
        req = {
            self.conf['ACTION']: self.conf['GET_USERS'],
            self.conf['TIME']: ctime(),
            self.conf['ACCOUNT_NAME']: username
        }
        send_message(sock, req)
        print(sock)
        answer = get_message(sock)
        if self.conf['RESPONSE'] in answer and answer[self.conf['RESPONSE']] == 202:
            return answer[self.conf['DATA_LIST']]
        else:
            raise ServerError

    # @log_client
    def contacts_list_request(self, sock, name):
        """Метод класса для запроса листа контактов"""
        self.client_logger.debug(f'Запрос контакт листа для пользователя {name}')
        req = {
            self.conf['ACTION']: self.conf['GET_CONTACTS'],
            self.conf['TIME']: ctime(),
            self.conf['USER_NAME']: name
        }
        self.client_logger.debug(f'Сформирован запрос {req}')
        send_message(sock, req)
        answer = get_message(sock)
        self.client_logger.debug(f'Получен ответ {answer}')
        if self.conf['RESPONSE'] in answer and answer[self.conf['RESPONSE']] == 202:
            return answer[self.conf['DATA_LIST']]
        else:
            raise ServerError

    # @log_client
    def load_db(self, sock, database, username):
        """Метод класса инициирует базу данных"""
        try:
            users_list = self.user_list_request(sock, username)
        except ServerError:
            self.client_logger.error('Ошибка запроса списка известных пользователей.')
        else:
            database.add_users(users_list)
        try:
            contacts_list = self.contacts_list_request(sock, username)
        except ServerError:
            self.client_logger.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                database.add_contact(contact)

    def main(self):
        """Главный метод класса, который запускает обе части клеентов"""
        print('Старт клиентского модуля.')
        data_connect_server = self.data_connect_serv()
        addr_server, port_server, name_client = data_connect_server['addr_server'], \
            data_connect_server['port_server'], data_connect_server['name_client']
        self.client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                                f'порт: {port_server}, имя пользователя {name_client}.')

        try:
            server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
            server_sock.settimeout(1.2)
            server_sock.connect((data_connect_server['addr_server'], data_connect_server['port_server']))
            message_to_serv = self.request_presence(name_client)
            self.client_logger.info(f'Сообщение для сервера сформировано успешно.')
            send_message(server_sock, message_to_serv, self.conf_name)
            self.client_logger.info(f'Сообщение для сервера отправлено успешно.')
            answer = self.get_answer(server_sock)
            self.client_logger.info(f'Пришёл ответ от сервера - {answer}')
            print('Соединение с сервером установлено.')
        except (ConnectionRefusedError, ConnectionError):
            self.client_logger.critical(f'Подключение к серверу {addr_server}:{port_server} не удалось!')
            exit(1)
        except ServerError as error:
            self.client_logger.error(f'При установлении соединения сервер вернул ошибку: {error.text}')
            exit(1)
        else:
            dir_path = dirname(realpath(__file__))
            data_base = ClientStorage(dir_path)
            self.load_db(server_sock, data_base, name_client)

            module_addresser = ClientAddresser(name_client, server_sock, data_base)
            module_addresser.daemon = True
            module_addresser.start()

            module_receiver = ClientReader(name_client, server_sock, data_base)
            module_receiver.daemon = True
            module_receiver.start()

            while True:
                sleep(1.2)
                if module_receiver.is_alive() and module_addresser.is_alive():
                    continue
                break


class ClientAddresser(Client, Thread, metaclass=ClientVerifier):
    """Класс клиента отвечающий за отправку сообщений"""

    def __init__(self, client, sock, db):
        self.client_name = client
        self.socket = sock
        self.data_base = db
        super().__init__()

    # @log_client
    def create_out_message(self, account):
        """Функция возвращает словарь с сообщением о выходе"""
        return {
            self.conf['ACTION']: self.conf['OUT'],
            self.conf['TIME']: ctime(),
            self.conf['ACCOUNT_NAME']: account
        }

    # @log_client
    def create_message(self, serv_sock, account):
        """Возвращает введённое сообщение"""
        target_user = input('Введите имя пользователя:\n')
        message = input('Введите текст сообщения или команду --> для завершения работы:\n')

        # проверка зарегистрирован ли получатель
        with db_lock:
            if not self.data_base.checker_contact(target_user):
                self.client_logger.error(f'Попытка передать сообщение '
                                         f'незарегистрированому получателю: {target_user}')
                return

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

        # сохранение сообщения для истории сообщений
        with db_lock:
            self.data_base.save_message(account, target_user, message)

        # дожидаемся чтоб сокет был освобождён
        with socket_lock:
            try:
                send_message(serv_sock, data_message, self.conf_name)
                self.client_logger.debug(f'Сообщение для пользователя {target_user} отправлено успешно')
            except Exception as err:
                self.client_logger.critical(f'{err}, соединение с сервером было потеряно')
                exit(1)

    @staticmethod
    def help_for_user():
        """Функция для вывода списка всех возможных команд для пользователя"""
        return 'Список доступных команд:\nsend - написать и отправить сообщение\n' \
               'help - вывести список доступных команд\nexit - завершить работу программы\n' \
               'history - вывести историю сообщений\nlist_contact - вывести список контактов\n' \
               'edit_contacts - редактирование списка контактов'

    def run(self, sock, user_name):
        """Функция для интерактивного взаимодействия с пользователем, функции: запрос команд"""
        while True:
            command = input('Ведите команду: ')
            if command == 'help':
                help_str = self.help_for_user()
                print(help_str)
            elif command == 'send':
                self.create_message(sock, user_name)
            elif command == 'exit':
                with socket_lock:
                    try:
                        send_message(sock, self.create_out_message(user_name), self.conf_name)
                    except Exception as err:
                        self.client_logger.error(f'{err}, ошибка отправки сообщения о выходе для {user_name}!')
                    print('Соединение было завершено.')
                    self.client_logger.info('Пользователь завершил работу программы командой.')
                sleep(0.7)
                break
            elif command == 'list_contact':
                with db_lock:
                    contacts_list = self.data_base.get_user_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit_contacts':
                self.edit_contacts()
            elif command == 'history':
                self.history_print()
            else:
                print('Команда не найдена! Для вывода списка доступных команд введите - help.')

    # @log_client
    def add_contact(self, sock, username, contact):
        """Метод класса добавляющий пользователя в список контактов"""
        self.client_logger.debug(f'Попытка создать контакт - {contact}')
        req = {
            self.conf['ACTION']: self.conf['ADD_CONTACT'],
            self.conf['TIME']: ctime(),
            self.conf['USER_NAME']: username,
            self.conf['ACCOUNT_NAME']: contact
        }
        send_message(sock, req)
        answer = get_message(sock)
        if self.conf['RESPONSE'] in answer and answer[self.conf['RESPONSE']] == 200:
            pass
        else:
            raise ServerError('Ошибка создания контакта')
        print('Контакт создан успешно.')

    # @log_client
    def edit_contacts(self):
        """Метод класса для редактирования контактов"""
        command = input('Введите delete для удаления или add добавления: ')
        if command == 'delete':
            edit_contact = input('Введите имя контакта для удаления: ')
            with db_lock:
                if self.data_base.checker_contact(edit_contact):
                    self.data_base.delete_contact(edit_contact)
                else:
                    self.client_logger.error(f'Попытка удаления несуществующего контакта {edit_contact}.')
        elif command == 'add':
            edit_contact = input('Введите имя добавляемого контакта: ')
            if self.data_base.check_user(edit_contact):
                with db_lock:
                    self.data_base.add_contact(edit_contact)
                with socket_lock:
                    try:
                        self.add_contact(self.socket, self.client_name, edit_contact)
                    except ServerError:
                        self.client_logger.error('Не удалось отправить данные на сервер.')

    # @log_client
    def history_print(self):
        """Метод класса для вывода истории сообщений"""
        command = input('Показать входящие сообщения - incoming, исходящие - outgoing, все - all: ')
        with db_lock:
            if command == 'incoming':
                history_list = self.data_base.get_history_messages(for_who=self.client_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif command == 'outgoing':
                history_list = self.data_base.get_history(from_who=self.client_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.data_base.get_history_messages()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')


class ClientReader(Client, Thread, metaclass=ClientVerifier):
    """Класс клиента отвечающий за чтение сообщений"""

    def __init__(self, client, sock, db):
        self.client_name = client
        self.socket = sock
        self.data_base = db
        super().__init__()

    def run(self):
        """Метод класса отвечающий за запуск и работу клиента"""
        while True:
            sleep(1.2)
            with socket_lock:
                try:
                    message = get_message(self.socket)
                except (ConnectionRefusedError, ConnectionError, ConnectionAbortedError, JSONDecodeError):
                    self.client_logger.critical(f'Соединение с сервером было потеряно!')
                except OSError as err:
                    if err.errno:
                        self.client_logger.critical(f'Соединение с сервером было потеряно!')
                        break
                # если сообщение корректное
                else:
                    if self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['MESSAGE'] \
                            and self.conf['ADDRESSER'] in message and self.conf['TARGET'] in message \
                            and self.conf['MESS_TEXT'] in message and message[self.conf['TARGET']] == self.client_name:
                        print(f'\n Получено сообщение от пользователя '
                              f'{message[self.conf["ADDRESSER"]]}:\n{message[self.conf["MESS_TEXT"]]}')
                        # Сохранение в бд сообщения
                        with db_lock:
                            try:
                                self.data_base.save_message(message[self.conf['ADDRESSER']], self.client_name,
                                                            message[self.conf['MESS_TEXT']])
                            except Exception as err:
                                print(err)
                                self.client_logger.error('Ошибка взаимодействия с базой данных')

                        self.client_logger.info(f'Получено сообщение от пользователя '
                                                f'{message[self.conf["ADDRESSER"]]}:'
                                                f'\n{message[self.conf["MESS_TEXT"]]}')
                    else:
                        self.client_logger.error(f'Получено некорректное сообщение с сервера: {message}')


client = Client()
client.main()

if __name__ == '__main__':
    client = Client()
    client.main()
