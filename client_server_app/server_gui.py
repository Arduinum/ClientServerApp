from sys import argv
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


def gui_create(db):
    """Функция создаст таблицу для подключений gui"""
    list_users = db.get_list_data('active_users')
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


def create_history_mess(db):
    """Функция для заполнения истории сообщений"""
    hist_list = db.get_message_count()
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Клиент', 'Последний вход', 'Отправил сообщений', 'Получил сообщений'])
    print(hist_list)
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


class MainWindow(QMainWindow):
    """Класс основное окно"""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """Метод класса для инициализации"""
        # кнопка для выхода
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # Кнопка для обновления списка клиентов
        self.refresh_button = QAction('Обновить список клиентов', self)

        # Кнопка вывода истории сообщений
        self.show_history_button = QAction('История клиентов', self)

        # Кнопка для настроек сервера
        self.config_btn = QAction('Настройки сервера', self)

        # Статусбар
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)

        # Настройки для геометрии основного окна
        self.setFixedSize(800, 700)
        self.setWindowTitle('Server for messaging alpha version')

        # Надпись о списке подключённых клиентов
        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        # отображение окна
        self.show()


class HistoryUsersWindow(QDialog):
    """Класс окно история пользователей"""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """Метод класса для инициализации"""
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 750)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка для закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class SettingsWindow(QDialog):
    """Класс окно настроек"""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """Метод класса для инициализации"""
        self.setFixedSize(365, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Строка с до базы данных
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор', self)
        self.db_path_select.move(275, 28)

        def open_file_handler():
            """Функция для обработки открытия окна с выбором папки"""
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_handler)

        # Метка с именем поля файла бд
        self.db_file_label = QLabel('Имя для файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # Метка с номером порта
        self.port_label = QLabel('Номер порта для соединения:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        # Метка с адресом для соединения
        self.ip_label = QLabel('IP для приёма соединений:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставить поле пустым, чтобы\n принимать соединения с любого адреса.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip адреса
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(190, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    my_app = QApplication(argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage('Test Statusbar Message')
    list_test = QStandardItemModel(main_window)
    list_test.setHorizontalHeaderLabels(['Клиент', 'IP', 'Порт', 'Время подключения'])
    list_test.appendRow(
        [QStandardItem('test_1'), QStandardItem('0.0.0.1'), QStandardItem('27598'), QStandardItem('19:40:54')])
    list_test.appendRow(
        [QStandardItem('test_2'), QStandardItem('192.160.0.6'), QStandardItem('43558'), QStandardItem('19:43:00')])
    main_window.active_clients_table.setModel(list_test)
    main_window.active_clients_table.resizeColumnsToContents()
    my_app.exec_()
    #
    # my_app = QApplication(argv)
    # history_window = HistoryUsersWindow()
    # list_test = QStandardItemModel(history_window)
    # list_test.setHorizontalHeaderLabels(
    #     ['Клиент', 'Последний вход', 'Отправлено сообщений', 'Получено сообщений'])
    # list_test.appendRow(
    #     [QStandardItem('test_1'), QStandardItem('Mon June 6 12:48:22 2022'), QStandardItem('4'), QStandardItem('5')])
    # list_test.appendRow(
    #     [QStandardItem('test_2'), QStandardItem('Mon June 6 12:49:11 2022'), QStandardItem('3'), QStandardItem('2')])
    # history_window.history_table.setModel(list_test)
    # history_window.history_table.resizeColumnsToContents()
    # my_app.exec_()

    my_app = QApplication(argv)
    dial = SettingsWindow()
    my_app.exec_()
