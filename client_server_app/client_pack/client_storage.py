from sys import path as sys_path
sys_path.append('../')
from os.path import dirname, realpath
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from common.utils import read_conf
from common.config_path_file import CONFIG_CLIENT_PATH


class ClientStorage:
    """Класс для работы с базой данных клиента в декларативном стиле"""
    Base = declarative_base()

    class FamousUsers(Base):
        """Класс известные для клиента пользователи"""
        __tablename__ = 'famous_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)

        def __init__(self, login):
            self.login = login
            super().__init__()

    class HistoryMessages(Base):
        """Класс история сообщений"""
        __tablename__ = 'history_messages'
        id = Column(Integer, primary_key=True)
        contact_login = Column(String)
        type_message = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, contact_login, type_message, message):
            self.contact_login = contact_login
            self.type_message = type_message
            self.message = message
            self.date = datetime.now()
            super().__init__()

    class UserContacts(Base):
        """Класс контакты пользователя"""
        __tablename__ = 'user_contacts'
        id = Column(Integer, primary_key=True)
        contact_login = Column(String, unique=True)

        def __init__(self, contact_login):
            self.contact_login = contact_login
            super().__init__()

    def __init__(self, path, name):
        # установка соединения с бд и сбор конф информации
        # echo=True - ведение лога, poll_recycle=7200 - переустановка соединения с бд каждые 2 часа
        self.engine = create_engine(f'sqlite:///{path}/{name}.db3', echo=True, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)  # создаём все таблицы
        session_fabric = sessionmaker(bind=self.engine)
        self.session = session_fabric()  # создаём сессию

        self.session.query(self.UserContacts).delete()
        self.session.commit()

    def table_clear(self, command):
        """Метод класса для очищения таблиц от данных"""
        try:
            if command == 'all':
                self.session.query(self.FamousUsers).delete()
                self.session.query(self.HistoryMessages).delete()
                self.session.query(self.UserContacts).delete()
                self.session.commit()
            else:
                eval(f'self.session.query(self.{command}).delete()')
                self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def add_contact(self, user):
        """Метод класса для добавления нового контакта"""
        try:
            if not self.session.query(self.UserContacts).filter_by(contact_login=user).count():
                new_contact = self.UserContacts(user)
                self.session.add(new_contact)
                self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def delete_contact(self, user):
        """Метод класса для удаления контакта из контактов клиента"""
        try:
            del_contact = self.session.query(self.UserContacts).filter_by(contact_login=user)
            if del_contact.count():
                del_contact.delete()
                self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def add_users(self, users_list):
        """Метод класса для добавления известных пользователей"""
        try:
            self.session.query(self.FamousUsers).delete()
            for user in users_list:
                if not self.session.query(self.FamousUsers).filter_by(login=user).count():
                    new_user = self.FamousUsers(user)
                    self.session.add(new_user)
                    self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def save_message(self, from_user, for_user, message):
        """Метод класса для сохранения сообщения"""
        try:
            new_message = self.HistoryMessages(from_user, for_user, message)
            self.session.add(new_message)
            self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def get_user_contacts_id(self):
        """Метод класса возвращает список контактов пользователя в виде id"""
        return [user[0] for user in self.session.query(self.UserContacts.contact_login).all()]

    def get_user_contacts(self):
        """Метод класса возвращает список контактов пользователя"""
        list_contact = list()
        contact_login_id_list = [user_id[0] for user_id in self.session.query(
            self.UserContacts.contact_login).all()]
        for user_id in contact_login_id_list:
            name_search = self.session.query(self.FamousUsers.login).filter_by(id=user_id)
            for name in name_search:
                list_contact.append(name[0])
        return list_contact

    def get_users(self):
        """Метод класса возращает список известных пользователей"""
        return [user[0] for user in self.session.query(self.FamousUsers.login).all()]

    def get_user_cont_id(self, contact_login):
        """Метод класса возвращает id контакта пользователя"""
        contact_login_id = [login[0] for login in self.session.query(
            self.FamousUsers.id).filter_by(login=contact_login)][0]
        return [user_id[0] for user_id in self.session.query(
            self.UserContacts.contact_login).filter_by(contact_login=contact_login_id)][0]

    def checker_user(self, login):
        """Метод класса для проверки известный ли клиенту пользователь"""
        if self.session.query(self.FamousUsers).filter_by(login=login).count():
            return True
        else:
            return False

    def checker_contact(self, contact_login):
        """Метод класса проверяет есть ли контакт в контактах"""
        contact_login_id = self.session.query(self.FamousUsers.id).filter_by(login=contact_login)
        if self.session.query(self.UserContacts).filter_by(contact_login=contact_login_id).count():
            return True
        else:
            return False

    def get_history_messages(self, contact):
        """Метод класса возращает историю сообщений"""
        history = self.session.query(self.HistoryMessages).filter_by(contact_login=contact)
        return [(history_line.contact_login, history_line.type_message, history_line.message, history_line.date)
                for history_line in history.all()]


if __name__ == '__main__':
    dir_path = dirname(realpath(__file__))
    client_storage = ClientStorage(dir_path, 'cl1')
    client_storage.table_clear('all')
    client_storage = ClientStorage(dir_path, 'cl2')
    client_storage.table_clear('all')
    # client_storage.add_contact('bot628')
    # client_storage.add_contact('botT1000')
    # client_storage.add_contact('WalleT34')
    # client_storage.delete_contact('bot628')
    # print(client_storage.get_user_contacts())
    # client_storage.add_users(['bot628', 'botT1000', 'WalleT34'])
    # print(client_storage.get_users())
    # client_storage.save_message('WalleT34', 'botT1000', 'Hello botT1000')
    # print(client_storage.checker_contact('botT1000'))
    # print(client_storage.get_history_messages(from_who='WalleT34'))
