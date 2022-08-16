from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt


class DelUser(QDialog):
    """Класс для выбора контакта в интерфейсе gui"""

    def __init__(self, data_base, server):
        super().__init__()
        self.data_base = data_base
        self.server = server

        self.setFixedSize(350, 120)
        self.setWindowTitle('Удалить пользователя')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Нужно выбрать пользователя для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.ok_button = QPushButton('Удалить', self)
        self.ok_button.setFixedSize(100, 30)
        self.ok_button.move(230, 20)
        self.ok_button.clicked.connect(self.del_user)

        self.cancel_button = QPushButton('Отменить', self)
        self.cancel_button.setFixedSize(100, 30)
        self.cancel_button.move(230, 60)
        self.cancel_button.clicked.connect(self.close)

        self.fill_users()

        self.show()

    def fill_users(self):
        """Метод класса заполняющий список пользователей"""
        self.selector.addItems([item[0] for item in self.data_base.get_list_data('users')])

    def del_user(self):
        """Метод класса для удаления пользователя (обработчик)"""
        self.data_base.delete_user(self.selector.currentText())
        if self.selector.currentText() in self.server.client_names:
            sock = self.server.client_names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)
        # рассылка клиентам чтоб обновили справочники
        self.server.service_updater_lists()
        self.close()


if __name__ == '__main__':
    from server_storage import ServerStorage
    from os.path import join
    from os import getcwd
    import sys
    from kernel import MessageReceiver

    my_app = QApplication(list())
    database = ServerStorage('./', 'server_data.db3')
    my_path = join(getcwd(), '..')
    sys.path.insert(0, my_path)
    server_test = MessageReceiver('127.0.0.1', 7777, database)
    dial = DelUser(database, server_test)
    my_app.exec_()
