from base64 import b64decode, b64encode
from json import JSONDecodeError
from sys import path as sys_path
from Cryptodome.PublicKey import RSA
from common.config_path_file import CONFIG_PATH
sys_path.append('../')
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from client_pack.main_window_conv import Ui_MainClientWindow
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication
from sys import argv, exit
from client_pack.add_contact import AddContactDialog
from client_pack.remove_contact import RemoveContactDialog
from common.erros import ServerError
from common.utils import client_log_config, read_conf
from logging import getLogger
from Cryptodome.Cipher import PKCS1_OAEP


client_logger = getLogger('client')
conf = read_conf(CONFIG_PATH)


class ClientMainWindow(QMainWindow):
    """Класс основного окна клиента"""
    def __init__(self, data_base, client_addresser, keys):
        super().__init__()
        self.data_base = data_base
        self.client_addresser = client_addresser

        self.select_dialog = None
        self.remove_dialog = None

        self.current_chat_key = None
        self.decrypter = PKCS1_OAEP.new(keys)
        self.cryptographer = None

        # загрузка конфигурации главного окна
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # кнопка - выход
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # кнопка - отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # кнопка - добавить контакт
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # кнопка - удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.del_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.del_contact_window)

        # доп атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None  # Текущий контакт для обмена сообщениями
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_act_user)
        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def send_message(self):
        """Метод класса для отправки сообщения пользователю"""
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return

        # шифрование сообщения ключом получателя и упаковка в base64
        message_text_encrypt = self.cryptographer.encrypt(message_text.encode('utf8'))
        message_text_encrypt_base64 = b64encode(message_text_encrypt)

        try:
            self.client_addresser.send_message(self.current_chat, message_text_encrypt_base64.decode('ascii'))
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Было потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Было потеряно соединение с сервером!')
            self.close()
        else:
            self.data_base.save_message(self.current_chat, 'out', message_text)
            client_logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_updater()

    def add_contact(self, new_contact):
        """Метод класса для добавления контакта в бд"""
        try:
            self.client_addresser.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Было потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.data_base.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            client_logger.info(f'Контакт {new_contact} был добавленю')
            self.messages.information(self, 'Успешно', 'Контакт был добавлен.')

    def add_cont_action(self, item):
        """Метод класса обработчик добавления контактов"""
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact_window(self):
        """Метод класса для добавления контакта gui"""
        self.select_dialog = AddContactDialog(self.client_addresser, self.data_base)
        self.select_dialog.ok_button.clicked.connect(lambda: self.add_cont_action(self.select_dialog))
        self.select_dialog.show()

    def del_contact(self, item):
        """Метод класса для удаления контакта"""
        selected = item.selector.currentText()
        selected_id = self.data_base.get_user_cont_id(selected)

        try:
            self.client_addresser.dell_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Было потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.data_base.delete_contact(selected_id)
            self.clients_list_update()
            client_logger.info(f'Контакт {selected} был удалён')
            self.messages.information(self, 'Успешно', 'Контакт был удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def del_contact_window(self):
        """Метод класса для удаления контакта gui"""
        self.remove_dialog = RemoveContactDialog(self.data_base)
        self.remove_dialog.ok_button.clicked.connect(lambda: self.del_contact(self.remove_dialog))
        self.remove_dialog.show()

    def select_act_user(self):
        """Метод класса обработчик для выбора контакта двойным нажатием"""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_act_user()

    def set_act_user(self):
        """Метод класса для выбора активного пользователя"""
        # запрос публичного ключа пользователя и создания объекта шифрования
        try:
            self.current_chat_key = self.client_addresser.key_pub_request(self.current_chat)
            client_logger.debug(f'Загружен публичный ключ для {self.current_chat}')
            if self.current_chat_key:
                self.cryptographer = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, JSONDecodeError):
            self.current_chat_key = None
            self.cryptographer = None
            client_logger.debug(f'Ключ не был получен для {self.current_chat}')

        # если ключ не был найден
        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка!', 'Нет ключа шифрования для выбронного вами пользователя!.')
            return

        # ставит надпись и активирует кнопки
        self.ui.label_new_message.setText(f'Введите сообщение для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_updater()

    def clients_list_update(self):
        """Метод класса для обновления листа контактов"""
        contacts_list = self.data_base.get_user_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def set_disabled_input(self):
        """Метод класса для выбора получателя сообщения"""
        self.ui.label_new_message.setText('Для выбора получателя нужно клинуть на нём дважды в окене контактов')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопки не активны.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.current_chat = None
        self.current_chat_key = None
        self.cryptographer = None

    def history_list_updater(self):
        """Метод класса заполняющий историю сообщений"""
        list_messages = sorted(self.data_base.get_history_messages(self.current_chat), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        length = len(list_messages)
        counter = 0

        if length > 22:
            counter = length - 20

        for i in range(counter, length):
            item = list_messages[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее сообщение от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            elif item[1] == 'out':
                mess = QStandardItem(f'Исходящее сообщение от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    @pyqtSlot(dict)
    def message_receiver(self, message):
        """Метод класса проверяющий входящие сообщения, дешефрует сообщения, сохраняет в историю сообщений"""
        encrypt_message = b64decode(message[conf['MESS_TEXT']])  # строка байт
        try:
            decrypt_message = self.decrypter.decrypt(encrypt_message)  # расшифрованная строка байт
        except (ValueError, TypeError):
            self.messages.warning(self, 'Ошибка!', 'Сообщение не удалось декодировать!.')
            return

        sender = message[conf['ADDRESSER']]

        if sender == self.current_chat:
            # расшифрованная строка
            self.data_base.save_message(self.current_chat, 'in', decrypt_message.decode('utf8'))
            self.history_list_updater()
        else:
            #  проверка есть ли пользователь в контактах
            if self.data_base.checker_contact(sender):
                if self.messages.question(self, 'Новое сообщение', f'Вам пришло новое сообщение от {sender}, '
                                          f'открыть чат с ним?', QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.data_base.save_message(self.current_chat, 'in', decrypt_message.decode('utf8'))
                    self.set_act_user()
            else:
                if self.messages.question(self, 'Новое сообщение', f'Вам пришло новое сообщение от {sender}.\n '
                                          f'Данного пользователя нет в ваших контактах.\n'
                                          f' Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.data_base.save_message(self.current_chat, 'in', decrypt_message.decode('utf8'))
                    self.set_act_user()

    @pyqtSlot()
    def connect_lost(self):
        """Метод класса, отвечающий за потерю соединения"""
        self.messages.warning(self, 'Сбой соединения!', 'Было потеряно соединение с сервером!')
        self.close()

    @pyqtSlot()
    def signal_205(self):
        """Метод класса слот, обнавляющий бд по команде сервера"""
        if self.current_chat and not self.data_base.checker_user(self.current_chat):
            self.messages.warning(self, 'Сожалеем', 'Ваш собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def do_connection(self, transport):
        """Метод класса, отвечающий за соединение"""
        transport.new_message.connect(self.message_receiver)
        transport.connect_lost.connect(self.connect_lost)
        transport.mess_205.connect(self.signal_205)


if __name__ == '__main__':
    from client_storage import ClientStorage
    from os.path import dirname, realpath

    app = QApplication(argv)
    dir_path = dirname(realpath(__file__))
    database = ClientStorage(dir_path, 'test_1')

    class Test1:
        client_name = 'test_1'

    window = ClientMainWindow(database, Test1, None)
    exit(app.exec_())
