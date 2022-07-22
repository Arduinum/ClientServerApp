#!../venv/bin/python3
from sys import argv, exit
from PyQt5.QtWidgets import QApplication
from client_pack.start_dialog import ClientNameDialog
from client_pack.transport import ClientTransport
from common.utils import log_client
from logging import getLogger
from client_pack.main_window import ClientMainWindow
from server import ServerError
from client_pack.client_storage import ClientStorage
from common.config_path_file import CONFIG_PATH
from common.utils import read_conf
from re import search


client_logger = getLogger('client')
conf = read_conf(CONFIG_PATH)


@log_client
def check_argv(arg_name):
    """Проверяет с префиксами вводят аргумент команды или без префикса и возращает аргумент команды"""
    client_logger.debug('Проверка аргументов')
    pattern_ip = r'\d+.\d+.\d+.\d+'
    try:
        if arg_name == 'addr':
            if '-a' in argv:
                return argv[argv.index('-a') + 1]
            elif '--addr' in argv:
                return argv[argv.index('--addr') + 1]
            else:
                for arg in argv:
                    if search(pattern_ip, arg):
                        return arg
                return conf['ADDR_DEF']
        elif arg_name == 'port':
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
                    return conf['PORT_DEF']
        elif arg_name == 'name':
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
    except IndexError as err:
        raise err


def main():
    """Функция запуска клиента"""
    client_logger.debug('Получение корректных данных для соединения с сервером')
    addr_server, port_server, name_client = check_argv('addr'), check_argv('port'), check_argv('name')
    # создание приложение клиент
    client_app = QApplication(argv)

    # если имя не указали запросим
    if not name_client:
        start_dialog = ClientNameDialog()
        client_app.exec_()
        # если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект.
        if start_dialog.ok_flag:
            name_client = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    client_logger.info(f'Старт работы клиента с параметрами: адрес сервера - {addr_server}, '
                       f'порт: {port_server}, имя пользователя {name_client}.')

    data_base = ClientStorage(name_client)

    # cоздание объекта транспорт и запуск транспортного потока
    transport = None
    try:
        transport = ClientTransport(port_server, addr_server, data_base, name_client)
        transport.daemon = True
        transport.start()
    except ServerError as err:
        print(err.text)
        exit(1)

    # создаём GUI
    main_window = ClientMainWindow(data_base, transport)
    main_window.do_connection(transport)
    main_window.setWindowTitle(f'Программа Чат alpha version - {name_client}')
    client_app.exec_()
    # при закрытом gui, закрываем транспорт
    transport.transport_close()
    transport.join()

# main()


if __name__ == '__main__':
    main()
