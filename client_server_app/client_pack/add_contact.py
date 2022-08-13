from sys import path as sys_path
sys_path.append('../')
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from logs import client_log_config
from logging import getLogger


class AddContactDialog(QDialog):
    """Класс добавление контакта для gui"""

    def __init__(self, client_addresser, data_base):
        super().__init__()
        self.data_base = data_base
        self.client_addresser = client_addresser
        self.client_logger = getLogger('client')

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выбор контакта для добавления:')
        # удаление диалога, если окно было закрыто преждевременно
        self.setAttribute(Qt.WA_DeleteOnClose)
        # сделать окно поверх других окон
        self.setModal(True)

        self.selector_label = QLabel('Выбор контакта для добавления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.refresh_button = QPushButton('Обновление списка', self)
        self.refresh_button.setFixedSize(126, 30)
        self.refresh_button.move(60, 60)

        self.ok_button = QPushButton('Добавить контакт', self)
        self.ok_button.setFixedSize(116, 30)
        self.ok_button.move(230, 20)

        self.cancel_button = QPushButton('Отменить', self)
        self.cancel_button.setFixedSize(100, 30)
        self.cancel_button.move(230, 60)
        self.cancel_button.clicked.connect(self.close)

        # заполнить список возможных контактов
        self.potential_contacts_update()
        # назначить действие на кнопку обновить
        self.refresh_button.clicked.connect(self.update_potential_contacts)

    def potential_contacts_update(self):
        """Метод класса для заполнения списка всех возможных контактов"""
        self.selector.clear()
        # множество всех контактов и контактов клиента
        contacts_list = set(self.data_base.get_user_contacts_id())
        users_list = set(self.data_base.get_users())
        # удалим из списка самого себя
        users_list.remove(self.client_addresser.name_client)
        # добавляем список возможных контактов
        self.selector.addItems(users_list - contacts_list)

    def update_potential_contacts(self):
        """Метод класса для обновления известных пользоватей и обновления предполагаемых контактов"""
        try:
            self.client_addresser.user_list_request()
        except OSError:
            pass
        else:
            self.client_logger.debug('Выполнено обновление списка пользователя с сервера')
            self.potential_contacts_update()
