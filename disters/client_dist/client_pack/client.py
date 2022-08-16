#!../venv/bin/python3
from os import urandom
from os.path import dirname, realpath, exists
from sys import argv, exit
from Cryptodome.PublicKey.RSA import generate, import_key
from PyQt5.QtWidgets import QApplication
from client_pack.start_dialog import ClientNameDialog
from client_pack.transport import ClientTransport
from logging import getLogger
from client_pack.main_window import ClientMainWindow
from common.erros import ServerError
from client_pack.client_storage import ClientStorage
from common.config_path_file import CONFIG_CLIENT_PATH
from common.utils import check_port_argv, check_addr_argv, check_name_argv, check_passwd_argv, read_conf


client_logger = getLogger('client')
conf = read_conf(CONFIG_CLIENT_PATH)


def main():
    """Функция запуска клиента"""
    client_logger.debug('Получение корректных данных для соединения с сервером')
    addr_server, port_server, name_client, passwd_client = check_addr_argv(), check_port_argv(), check_name_argv(), \
        check_passwd_argv()
    # создание приложение клиент
    client_app = QApplication(argv)

    # если имя и/или пароль не указали запросим
    if not name_client or not passwd_client:
        start_dialog = ClientNameDialog()
        client_app.exec_()
        # если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект.
        if start_dialog.ok_flag:
            name_client = start_dialog.client_name.text()
            passwd_client = start_dialog.client_passwd.text()
            del start_dialog
            client_logger.debug(f'Используется логин - {name_client}, пароль - {passwd_client}.')
        else:
            exit(0)

    client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                       f'порт: {port_server}, имя пользователя {name_client}.')

    # читаем файл с ключом чтоб его получить, если его нет генерируется новая пара ключей
    dir_path = dirname(realpath(__file__))
    file_with_key = f'{dir_path}/{name_client}.key'
    if not exists(file_with_key):
        keys_rsa = generate(2048, urandom)
        with open(file_with_key, 'wb') as file:
            file.write(keys_rsa.export_key())
    else:
        with open(file_with_key, 'rb') as file:
            keys_rsa = import_key(file.read())

    client_logger.debug('Ключи успешно прочитаны.')

    data_base = ClientStorage(conf['DB_PATH'], name_client)

    # cоздание объекта транспорт и запуск транспортного потока
    transport = None
    try:
        transport = ClientTransport(port_server, addr_server, data_base, name_client, passwd_client, keys_rsa)
        transport.daemon = True
        transport.start()
    except ServerError as err:
        print(err.text)
        exit(1)

    # создаём GUI
    main_window = ClientMainWindow(data_base, transport, keys_rsa)
    main_window.do_connection(transport)
    main_window.setWindowTitle(f'Программа Чат alpha version - {name_client}')
    client_app.exec_()
    # при закрытом gui, закрываем транспорт
    transport.transport_close()
    transport.join()


if __name__ == '__main__':
    main()
