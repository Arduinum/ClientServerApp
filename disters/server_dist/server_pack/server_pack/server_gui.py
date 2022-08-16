from os.path import dirname, realpath
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView, QDialog, QPushButton, QLineEdit, \
    QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer
from common.config_path_file import CONFIG_PATH
from common.utils import read_conf, read_conf_lines, replace_value_list_conf
from yaml import dump
from server_pack.register_user import RegisterUser
from server_pack.remove_user import DelUser

conf = read_conf(CONFIG_PATH)


class MainWindow(QMainWindow):
    """Класс основное окно gui сервера"""
    def __init__(self, db, server):
        super().__init__()
        self.db = db
        self.server = server
        self.settings_window = None
        self.statist_window = None
        self.register_window = None
        self.delete_user = None
        self.dir_path = dirname(realpath(__file__))

        # кнопка для выхода
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # кнопка для обновления списка клиентов
        self.refresh_button = QAction('Обновить список клиентов', self)

        # кнопка вывода истории сообщений
        self.show_history_button = QAction('История клиентов', self)

        # кнопка для настроек сервера
        self.config_button = QAction('Настройки сервера', self)

        # кнопка регистрации пользователя
        self.register_button = QAction('Регистрация пользователя', self)

        # кнопка удаления пользователя
        self.del_button = QAction('Удалить пользователя', self)

        # статусбар
        self.statusBar()
        self.statusBar().showMessage('Server start Working')

        # тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(self.register_button)
        self.toolbar.addAction(self.del_button)

        # настройки для геометрии основного окна
        self.setFixedSize(800, 700)
        self.setWindowTitle('Server for messaging alpha version')

        # надпись о списке подключённых клиентов
        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        # таймер, который обновляет список клиентов раз в 1200 милсек
        self.timer = QTimer()
        self.timer.timeout.connect(self.updater_list)
        self.timer.start(1200)

        # связывание кнопок и процедур
        self.refresh_button.triggered.connect(self.updater_list)
        self.show_history_button.triggered.connect(self.print_statistics)
        self.config_button.triggered.connect(self.server_settings)
        self.register_button.triggered.connect(self.register_user)
        self.del_button.triggered.connect(self.del_user)

        # отображение окна
        self.show()

    def gui_create(self):
        """Метод класса создаст таблицу для подключений gui"""
        list_users = self.db.get_list_data('active_users')
        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(['Клиент', 'IP', 'Порт', 'Время подключения'])
        for line in list_users:
            user, ip, port, time = line
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))  # чтоб убрать миллисекунды
            time.setEditable(False)
            list_table.appendRow([user, ip, port, time])
        return list_table

    def updater_list(self):
        """Метод класса для обновления списка подключённых клиентов для gui"""
        self.active_clients_table.setModel(self.gui_create())
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def print_statistics(self):
        """Метод класса вывода статистики клиентов для gui"""
        self.statist_window = HistoryUsersWindow()
        self.statist_window.history_table.setModel(self.create_history_mess())
        self.statist_window.history_table.resizeColumnsToContents()
        self.statist_window.history_table.resizeRowsToContents()

    def create_history_mess(self):
        """Функция для заполнения истории сообщений"""
        hist_list = self.db.get_message_count()
        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(
            ['Клиент', 'Последний вход', 'Отправил сообщений', 'Получил сообщений'])
        for line in hist_list:
            user, last_seen, sent, received = line
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            received = QStandardItem(str(received))
            received.setEditable(False)
            list_table.appendRow([user, last_seen, sent, received])
        return list_table

    def server_settings(self):
        """Метод класса для создания окна настроек сервера gui"""
        self.settings_window = SettingsWindow()
        self.settings_window.db_path.insert(conf['DB_PATH'])
        self.settings_window.db_file.insert(conf['DB_NAME_FILE'])
        self.settings_window.port.insert(str(conf['PORT_DEF']))
        self.settings_window.ip.insert(conf['ADDR_LISTEN_DEF'])
        self.settings_window.save_btn.clicked.connect(self.save_server_settings)

    def save_server_settings(self):
        """Функция для сохранения настроек для gui"""
        message = QMessageBox()
        list_conf_lines = read_conf_lines(CONFIG_PATH)
        result_list = replace_value_list_conf(list_conf_lines, 'DB_PATH', self.settings_window.db_path.text())
        result_list = replace_value_list_conf(result_list, 'DB_NAME_FILE', self.settings_window.db_file.text())

        try:
            port = int(self.settings_window.port.text())
        except ValueError:
            message.warning(self.settings_window, 'Ошибка', 'порт должен быть числом!')
        else:
            result_list = replace_value_list_conf(result_list, 'ADDR_LISTEN_DEF', self.settings_window.ip.text())
            if 1023 < port < 65536:
                result_list = replace_value_list_conf(result_list, 'PORT_DEF', str(port))
                with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                    file.writelines(result_list)
                    message.information(self.settings_window, 'Успех', 'Настройки успешно сохранены!')
            else:
                message.warning(self.settings_window, 'Ошибка', 'допустимый диапазон чисел для порта от 1024 до 65536')

    def register_user(self):
        """Метод класса, который создаёт окно регистрации пользователя"""
        self.register_window = RegisterUser(self.db, self.server)

    def del_user(self):
        """Метод класса для удаления пользователя"""
        self.delete_user = DelUser(self.db, self.server)


class HistoryUsersWindow(QDialog):
    """Класс окно история пользователей"""
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 750)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # кнопка для закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class SettingsWindow(QDialog):
    """Класс окно настроек"""
    def __init__(self):
        super().__init__()

        self.setFixedSize(365, 260)
        self.setWindowTitle('Настройки сервера')

        # надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # строка с до базы данных
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор', self)
        self.db_path_select.move(275, 28)

        def open_file_handler():
            """Функция для обработки открытия окна с выбором папки"""
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_handler)

        # метка с именем поля файла бд
        self.db_file_label = QLabel('Имя для файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # метка с номером порта
        self.port_label = QLabel('Номер порта для соединения:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        # метка с адресом для соединения
        self.ip_label = QLabel('IP для приёма соединений:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставить поле пустым, чтобы\n принимать соединения с любого адреса.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # поле для ввода ip адреса
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(190, 220)

        # кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from sys import argv
    from server_pack.server_storage import ServerStorage
    from common.utils import read_conf, check_port_argv, check_addr_argv, check_gui_argv
    from server_pack.kernel import MessageReceiver

    database = ServerStorage()
    listen_port = check_port_argv()
    listen_addr = check_addr_argv()
    no_gui = check_gui_argv()

    serv = MessageReceiver(listen_addr, listen_port, database)

    server_gui = QApplication(argv)
    server_gui.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(database, serv)
    server_gui.exec_()

    # my_app = QApplication(list())
    # settings_window = SettingsWindow()
    # my_app.exec_()

    # my_app = QApplication(list())
    # history_window = HistoryUsersWindow()
    # my_app.exec_()


