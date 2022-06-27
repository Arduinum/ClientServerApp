#!../venv/bin/python3
from sys import argv
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from select import select
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from common.utils import get_message, send_message, read_conf
from time import ctime
from logging import getLogger
import logs.server_log_config
from common.utils import log
from descriptor import PortDescriptor
from metaclasses import ServerVerifier
from threading import Lock, Thread
from server_storage import ServerStorage
from server_gui import MainWindow, HistoryUsersWindow, SettingsWindow, gui_create, create_history_mess
from os.path import dirname, realpath
from yaml import dump


# флаг для определения подключенного нового пользователя (для экономии запросов к бд)
new_connect = False
flag_lock = Lock()


def get_item_args(name_arg):
    """Функция для поиска аргумента в списке аргументов"""
    conf_name = './common/config.yaml'
    conf = read_conf(conf_name)

    if name_arg == 'port':
        for p in argv:
            if p.isdigit():
                return int(p)
            elif p[0] == '-':
                if p[1:].isdigit():
                    return int(p)
        return conf['PORT_DEF']


class Server(Thread, metaclass=ServerVerifier):
    port_listen = PortDescriptor()

    def __init__(self, port, db):
        self.conf_name = './common/config.yaml'
        self.conf_serv_db_name = './common/config_server_db.yaml'
        self.conf = read_conf(self.conf_name)
        self.server_logger = getLogger('server')
        self.port_listen = port
        self.db = db
        self.client_names = dict()  # ключ имя пользователя значение сокет его клиента
        super().__init__()

    def work_server(self):
        """Отвечает за запуск и работу сервера"""
        addr_listen = self.get_address()

        if len(addr_listen) == 0:
            self.server_logger.info(f'Старт сервера на адресе 0.0.0.0:{self.port_listen}, использующимся для '
                                    f'подключения.')
        else:
            self.server_logger.info(
                f'Старт сервера на адресе {addr_listen}:{self.port_listen}, использующимся для подключения.')

        conf = read_conf(self.conf_name)
        server_sock = socket(AF_INET, SOCK_STREAM)  # создаём сокет TCP
        server_sock.bind((addr_listen, self.port_listen))  # присваиваем порт и адрес
        server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # устанавливаем опции сокета
        server_sock.settimeout(0.8)  # таймаут для операций с сокетом
        clients_list = list()
        messages_queue = list()
        server_sock.listen(conf['MAX_CONNECT'])  # слушаем порт

        while True:
            try:
                client, client_addr = server_sock.accept()
            except OSError:  # произойдёт если таймаут вышел
                date_now = ctime()
                print(f'{date_now} - timeout is over')
            else:
                self.server_logger.info(f'Пришёл запрос от клиента на соединение {client_addr}')
                clients_list.append(client)  # добавляем постучавшегося клиента

            r_list, w_list = [], []
            # проверка есть ли ждущие клиенты
            try:
                if len(clients_list) > 0:
                    r_list, w_list, e_list = select(clients_list, clients_list, [], 0)
            except OSError as err:
                self.server_logger.error(f'{err} - ошибка во время работы с сокетом!')

            # приём сообщений и исключение клиентов с ошибкой
            if len(r_list) > 0:
                for r_client in r_list:
                    try:
                        self.message_handler(get_message(r_client), messages_queue, r_client, clients_list,
                                             self.client_names)
                    except (Exception,):
                        self.server_logger.info(f'Клиент {r_client.getpeername()} отключился от сервера')
                        for name in self.client_names.keys():
                            if self.client_names[name] == r_client:
                                self.db.user_logout(name)
                                del self.client_names[name]
                        clients_list.remove(r_client)

            # обрабратываем сообщения если они есть
            for item in messages_queue:
                try:
                    self.message_for_target(item, self.client_names, w_list)
                except (Exception,):
                    self.server_logger.info(f'Соединение с клиентом {item[conf["TARGET"]]} было потеряно')
                    clients_list.remove(self.client_names[item[conf['TARGET']]])
                    self.db.user_logout(item[conf['TARGET']])
                    del self.client_names[item[conf['TARGET']]]
            messages_queue.clear()

    @log
    def message_handler(self, message, mess_list, client, clients, names):
        """Обрабатывает сообщения от клиентов"""
        global new_connect
        self.server_logger.debug(f'Обработка сообщения от клиента - {message}')
        # если сообщение о присутствии клиента
        if self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['PRESENCE'] and \
                self.conf['TIME'] in message and self.conf['USER_NAME'] in message:
            if message[self.conf['USER_NAME']][self.conf['ACCOUNT_NAME']] not in names.keys():
                client_now = message[self.conf['USER_NAME']][self.conf['ACCOUNT_NAME']]
                names[client_now] = client
                response = {self.conf['RESPONSE']: 200}
                send_message(client, response, conf_name=self.conf_name)
                self.server_logger.debug(f'Присутствие клиента {response} - {client}')
                with flag_lock:
                    new_connect = True
            else:
                response = {
                    self.conf['RESPONSE']: 400,
                    self.conf['ERROR']: 'Такое имя пользователя уже существует!'
                }
                send_message(client, response, conf_name=self.conf_name)
                clients.remove(client)
                client.close()
                self.server_logger.debug(f'Имя пользователя {message[self.conf["USER_NAME"]]} уже существует!')
            return
        # если это сообщение от пользователя
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['MESSAGE'] and \
                self.conf['TIME'] in message and self.conf['MESS_TEXT'] in message and self.conf['TARGET'] in message \
                and self.conf['ADDRESSER'] in message:
            mess_list.append(message)
            return
        # если клиент решил выйти
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['OUT'] and \
                self.conf['ACCOUNT_NAME'] in message:
            self.db.user_logout(self.conf['ACCOUNT_NAME'])
            self.server_logger.info(f'Клиент {self.conf["ACCOUNT_NAME"]} отключился от сервера')
            clients.remove(names[message[self.conf['ACCOUNT_NAME']]])
            names[message[self.conf['ACCOUNT_NAME']]].close()
            client_now = message[self.conf['ACCOUNT_NAME']]
            del names[client_now]
            with flag_lock:
                new_connect = True
            return
        # если делает запрос контакт
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['GET_CONTACTS'] \
                and self.conf['USER_NAME'] in message and self.client_names[message[self.conf['USER_NAME']]] == client:
            response = {
                self.conf['RESPONSE']: 202,
                self.conf['DATA_LIST']: self.db.get_users_contacts(message[self.conf['USER_NAME']])
            }
            send_message(client, response)
        # если запрос на добавление контакта
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['ADD_CONTACT'] \
                and self.conf['ACCOUNT_NAME'] in message and self.conf['USER_NAME'] in message \
                and self.client_names[message[self.conf['USER_NAME']]] == client:
            self.db.add_contact(message[self.conf['USER_NAME']], message[self.conf['ACCOUNT_NAME']])
            send_message(client, {self.conf['RESPONSE']: 200})
        # если запрос на удаление контакта
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['DEL_CONTACT'] \
                and self.conf['ACCOUNT_NAME'] in message and self.conf['USER_NAME'] in message \
                and self.client_names[message[self.conf['USER_NAME']]] == client:
            self.db.delete_contact(message[self.conf['USER_NAME']], message[self.conf['ACCOUNT_NAME']])
            send_message(client, {self.conf['RESPONSE']: 200})
        # если запрос от известного пользователя
        elif self.conf['ACTION'] in message and message[self.conf['ACTION']] == self.conf['GET_USERS'] \
                and self.conf['ACCOUNT_NAME'] in message \
                and self.client_names[message[self.conf['ACCOUNT_NAME']]] == client:
            response = {
                self.conf['RESPONSE']: 202,
                self.conf['DATA_LIST']: [user[0] for user in self.db.get_list_data('users')]
            }
            send_message(client, response)

        # иначе (если некорректный запрос)
        else:
            form_message = {
                self.conf['RESPONSE']: 400,
                self.conf['ERROR']: 'Bad Request'
            }
            send_message(client, form_message)
            return

    @log
    def get_address(self):
        """Возращает адрес для прослушивания сервером"""
        self.server_logger.debug(f'Получение адреса для прослушивания сервером из - {self.conf_name}')
        try:
            for i, addr in enumerate(argv):
                if addr == '-a':
                    self.server_logger.info(f'Получен адрес для прослушивания сервером - {argv[i + 1]}')
                    return argv[i + 1]
            self.server_logger.info('Для прослушивания сервером задан адрес по умолчанию - 0.0.0.0')
            return self.conf['ADDR_LISTEN_DEF']
        except IndexError:
            self.server_logger.critical('После параметра "-a" нужно указать адрес для прослушивания сервером!')

    @log
    def message_for_target(self, message, names, hear_socks):
        """Метод класса отправляющий сообщение определённому пользователю"""
        if message[self.conf['TARGET']] in names and names[message[self.conf['TARGET']]] in hear_socks:
            send_message(names[message[self.conf['TARGET']]], message, conf_name=self.conf_name)
            self.server_logger.info(f'Сообщение пользователю {message[self.conf["TARGET"]]} отправлено успешно.\n'
                                    f'Отправитель {message[self.conf["ADDRESSER"]]}.')
        elif message[self.conf['TARGET']] in names and names[message[self.conf['TARGET']]] not in hear_socks:
            raise ConnectionError
        else:
            self.server_logger.error(f'Пользователь {message[self.conf["TARGET"]]} должен пройти регистрацию!\n'
                                     f'Отправка сообщения доступна лишь зарегестрированным пользователям!')


def main():
    dir_path = dirname(realpath(__file__))
    database = ServerStorage(dir_path)
    listen_port = get_item_args('port')
    server = Server(listen_port, database)
    conf_db_serv = read_conf(server.conf_serv_db_name)
    server.daemon = True
    server.start()

    # # создаст gui для сервера
    # server_gui = QApplication(argv)
    # main_window = MainWindow()
    # # Инициализирует параметры для окон
    # main_window.statusBar().showMessage('Server start Working')
    # main_window.active_clients_table.setModel(gui_create(database))
    # main_window.active_clients_table.resizeColumnsToContents()
    # main_window.active_clients_table.resizeRowsToContents()

    # def updater_list():
    #     """Функция для обновления списка подключённых клиентов для gui"""
    #     global new_connect
    #     if new_connect:
    #         main_window.active_clients_table.setModel(
    #             gui_create(database))
    #         main_window.active_clients_table.resizeColumnsToContents()
    #         main_window.active_clients_table.resizeRowsToContents()
    #         with flag_lock:
    #             new_connect = False
    #
    # def print_statistics():
    #     """Функция вывода статистики клиентов для gui"""
    #     statist_window = HistoryUsersWindow()
    #     statist_window.history_table.setModel(create_history_mess(database))
    #     statist_window.history_table.resizeColumnsToContents()
    #     statist_window.history_table.resizeRowsToContents()
    #     statist_window.show()
    #
    # def server_settings():
    #     """Функция для создания окна настроек сервера"""
    #     global settings_window
    #     settings_window = SettingsWindow()
    #     settings_window.db_path.insert(dir_path)
    #     settings_window.db_file.insert(conf_db_serv['DB_NAME_FILE'])
    #     settings_window.port.insert(conf_db_serv['DEFAULT_PORT'])
    #     settings_window.ip.insert(conf_db_serv['LISTEN_ADDR'])
    #     settings_window.save_btn.clicked.connect(save_server_settings)
    #
    # def save_server_settings():
    #     """Функция для сохранения настроек для gui"""
    #     global settings_window
    #     message = QMessageBox()
    #     conf_db_serv['DB_PATH'] = settings_window.db_path.text()
    #     conf_db_serv['DB_NAME_FILE'] = settings_window.db_file.text()
    #     try:
    #         port = int(settings_window.port.text())
    #     except ValueError:
    #         message.warning(settings_window, 'Ошибка', 'порт должен быть числом!')
    #     else:
    #         conf_db_serv['LISTEN_ADDR'] = settings_window.ip.text()
    #         if 1023 < port < 65536:
    #             conf_db_serv['DEFAULT_PORT'] = str(port)
    #             print(port)
    #             with open(server.conf_serv_db_name, 'w', encoding='utf-8') as file:
    #                 dump(conf_db_serv, file, default_flow_style=False)
    #                 message.information(
    #                     settings_window, 'Успех', 'Настройки успешно сохранены!')
    #         else:
    #             message.warning(
    #                 settings_window,
    #                 'Ошибка',
    #                 'допустимый диапазон чисел для порта от 1024 до 65536')
    #
    # # Таймер, который обновляет список клиентов раз в 1200 милсек
    # timer = QTimer()
    # timer.timeout.connect(updater_list)
    # timer.start(1200)
    #
    # # Для связывания кнопки с процедурами
    # main_window.refresh_button.triggered.connect(updater_list)
    # main_window.show_history_button.triggered.connect(print_statistics)
    # main_window.config_btn.triggered.connect(server_settings)

    # Запуск gui
    # server_gui.exec_() # сервер и gui не работают вместе!
    # server.work_server()


# main()

if __name__ == '__main__':
    # listen_port = get_item_args('port')
    # database = ServerStorage()
    # server = Server(listen_port, database)
    # server.work_server()
    main()
