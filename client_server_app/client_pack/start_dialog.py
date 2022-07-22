from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp


class ClientNameDialog(QDialog):
    """Класс стартового диалога, для выбора имени пользователя"""
    def __init__(self):
        super().__init__()

        self.ok_flag = False
        self.setWindowTitle('Здравствуйте!')
        self.setFixedSize(175, 93)

        self.label = QLabel('Введите свое имя или ник: ', self)
        self.label.move(8, 10)
        self.label.setFixedSize(175, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.ok_button = QPushButton('Старт', self)
        self.ok_button.move(10, 60)
        self.ok_button.clicked.connect(self.click_ok)

        self.cancel_button = QPushButton('Выйти', self)
        self.cancel_button.move(90, 60)
        self.cancel_button.clicked.connect(qApp.exit)
        self.show()

    def click_ok(self):
        """Метод класса обработчик, следящий за вводом имени и нажатием кнопки ок"""
        if self.client_name.text():
            self.ok_flag = True
            qApp.exit()


if __name__ == '__main__':
    my_app = QApplication(list())
    dial = ClientNameDialog()
    my_app.exec_()
