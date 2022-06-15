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


class Server:
    def __init__(self):
        self.conf_name = './common/config.yaml'
        self.conf = read_conf(self.conf_name)
        self.server_logger = getLogger('server')

    @log
    def message_handler(self, message, mess_list, client, clients, names):
        """Обрабатывает сообщения от клиентов"""
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
            clients.remove(names[message[self.conf['ACCOUNT_NAME']]])
            names[message[self.conf['ACCOUNT_NAME']]].close()
            client_now = message[self.conf['ACCOUNT_NAME']]
            del names[client_now]
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
    def get_port(self):
        """Возращает корректный порт для прослушивания сервером"""
        self.server_logger.debug(f'Получение порта для прослушивания сервером из - {self.conf_name}')
        try:
            for i, port in enumerate(argv):
                if port == '-p':
                    if int(argv[i + 1]) < 1024 or int(argv[i + 1]) > 65535:
                        raise ValueError
                    self.server_logger.info(f'Получен порт для прослушивания сервером - {argv[i + 1]}')
                    return int(argv[i + 1])
            self.server_logger.info(f'Для прослушивания сервером задан порт по умолчанию - {self.conf["PORT_DEF"]}')
            return self.conf['PORT_DEF']
        except IndexError:
            self.server_logger.critical('После параметра "-p" нужно указать номер порта!')
            exit(1)
        except ValueError:
            self.server_logger.critical('Номер порта должен быть указан в диапазоне от 1024 до 65535!')
            exit(1)

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

    def work_server(self):
        """Отвечает за запуск и работу сервера"""
        addr_listen = self.get_address()
        port_listen = self.get_port()

        if len(addr_listen) == 0:
            self.server_logger.info(f'Старт сервера на адресе 0.0.0.0:{port_listen}, использующимся для подключения.')
        else:
            self.server_logger.info(
                f'Старт сервера на адресе {addr_listen}:{port_listen}, использующимся для подключения.')

        conf = read_conf(self.conf_name)
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
                self.server_logger.info(f'Пришёл запрос от клиента на соединение {client_addr}')
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
                        self.message_handler(get_message(r_client), messages_queue, r_client, clients_list,
                                             client_names)
                    except (Exception,):
                        self.server_logger.info(f'Клиент {r_client.getpeername()} отключился от сервера')
                        clients_list.remove(r_client)

            # обрабратываем сообщения если они есть
            for item in messages_queue:
                try:
                    self.message_for_target(item, client_names, w_list)
                except (Exception,):
                    self.server_logger.info(f'Соединение с клиентом {item[conf["TARGET"]]} было потеряно')
                    clients_list.remove(client_names[item[conf['TARGET']]])
                    del client_names[item[conf['TARGET']]]
            messages_queue.clear()


server = Server()
server.work_server()


if __name__ == '__main__':
    server = Server()
    server.work_server()
