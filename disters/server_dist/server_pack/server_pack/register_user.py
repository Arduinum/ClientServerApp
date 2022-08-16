from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, QMessageBox
from PyQt5.QtCore import Qt
import hashlib
import binascii

from logging import getLogger

server_logger = getLogger('server')


class RegisterUser(QDialog):
    """ Класс регистрации пользователя на сервере gui"""

    def __init__(self, data_base, server):
        super().__init__()

        self.data_base = data_base
        self.server = server

        self.setWindowTitle('Регистрация:')
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_login_name = QLabel('Введите ваше имя/ник:', self)
        self.label_login_name.move(10, 10)
        self.label_login_name.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel('Введите ваш пароль:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.label_config = QLabel('Введите подтверждение:', self)
        self.label_config.move(10, 100)
        self.label_config.setFixedSize(150, 15)

        self.client_config = QLineEdit(self)
        self.client_config.setFixedSize(154, 20)
        self.client_config.move(10, 120)
        self.client_config.setEchoMode(QLineEdit.Password)

        self.ok_button = QPushButton('Сохранить', self)
        self.ok_button.move(10, 150)
        self.ok_button.clicked.connect(self.data_saving)

        self.cancel_button = QPushButton('Выйти', self)
        self.cancel_button.move(90, 150)
        self.cancel_button.clicked.connect(self.close)

        self.messages = QMessageBox()
        self.show()

    def data_saving(self):
        """Метод класса для проверки правильности вводных данных и сохранения в бд нового пользователя"""
        if not self.client_name.text():
            self.messages.critical(self, 'Ошибка', 'Не было указано имя пользователя!')
            return
        elif self.client_passwd.text() != self.client_config.text():
            self.messages.critical(self, 'Ошибка', 'Введённые пароли не совпали!')
            return
        elif self.data_base.checker_user(self.client_name.text()):
            self.messages.critical(self, 'Ошибка', 'Такой пользователь уже существует!')
            return
        else:
            passwd_in_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            hash_passwd = hashlib.pbkdf2_hmac('sha512', passwd_in_bytes, salt, 10000)
            self.data_base.register_user(self.client_name.text(), binascii.hexlify(hash_passwd))
            self.messages.information(self, 'Успешно', 'Пользователь был успешно зарегистрирован.')
            # рассылка клиентам о необходимости обновления справочника
            self.server.service_updater_lists()
            self.close()


if __name__ == '__main__':
    from server_storage import ServerStorage
    from os import path, getcwd
    from sys import path as sys_path
    from kernel import MessageReceiver

    my_app = QApplication(list())
    dir_path = path.dirname(path.realpath(__file__))
    database = ServerStorage(dir_path, 'server_data.db3')
    my_path = path.join(getcwd(), '..')
    sys_path.insert(0, my_path)

    serv = MessageReceiver('127.0.0.1', 7777, database)
    dial = RegisterUser(database, serv)
    my_app.exec_()
