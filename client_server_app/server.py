#!../venv/bin/python3
from logging import getLogger
from sys import argv
from PyQt5.QtWidgets import QApplication
from common.config_path_file import CONFIG_PATH
from server_pack.server_gui import MainWindow
from server_pack.server_storage import ServerStorage
from common.utils import check_port_argv, check_addr_argv, check_gui_argv, read_conf
from common.decorators import log
from server_pack.kernel import MessageReceiver
from PyQt5.QtCore import Qt


server_logger = getLogger('server')
conf = read_conf(CONFIG_PATH)


@log
def main():
    database = ServerStorage()
    listen_port = check_port_argv()
    listen_addr = check_addr_argv()
    no_gui = check_gui_argv()

    server = MessageReceiver(listen_addr, listen_port, database)

    if no_gui:
        server.gui_on = False

    server.daemon = True
    server.start()

    # если указан флаг без gui
    if no_gui:
        while True:
            print('Старт косольной версии сервера.')
            command = input('Завершить работу сервера можно командой exit.\n')
            if command == 'exit':
                server.run_serv = False
                server.join()
                break
    else:
        # создаст gui для сервера
        server_gui = QApplication(argv)
        server_gui.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server)

        # Запуск gui
        server_gui.exec_()
        server.run_serv = False


if __name__ == '__main__':
    main()
