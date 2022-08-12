from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from sys import argv
from client_pack.client_storage import ClientStorage


class RemoveContactDialog(QDialog):
    """Класс gui для удаления контакта"""
    def __init__(self, data_base):
        super().__init__()
        self.data_base = data_base

        self.setFixedSize(350, 120)
        self.setWindowTitle('Какой контакт удалить: ')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт: ', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)
        self.selector.addItems(sorted(self.data_base.get_user_contacts()))

        self.ok_button = QPushButton('Удалить', self)
        self.ok_button.setFixedSize(100, 30)
        self.ok_button.move(230, 20)

        self.cancel_button = QPushButton('Отменить', self)
        self.cancel_button.setFixedSize(100, 30)
        self.cancel_button.move(230, 60)
        self.cancel_button.clicked.connect(self.close)


if __name__ == '__main__':
    my_app = QApplication(argv)
    database = ClientStorage('test_1')
    window = RemoveContactDialog(database)
    database.add_contact('test_1')
    database.add_contact('test_2')
    print(database.get_user_contacts())
    window.selector.addItems(sorted(database.get_user_contacts()))
    window.show()
    my_app.exec_()
