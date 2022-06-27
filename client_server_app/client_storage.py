from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime


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

    class HistoryMessages(Base):
        """Класс история сообщений"""
        __tablename__ = 'history_messages'
        id = Column(Integer, primary_key=True)
        from_user = Column(String)  # от кого сообщение
        for_user = Column(String)  # для кого сообщение
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, from_user, for_user, message):
            self.from_user = from_user
            self.for_user = for_user
            self.message = message
            self.date = datetime.now()

    class UserContacts(Base):
        """Класс контакты пользователя"""
        __tablename__ = 'user_contacts'
        id = Column(Integer, primary_key=True)
        contact_login = Column(String, unique=True)

        def __init__(self, contact_login):
            self.contact_login = contact_login

    def __init__(self):
        # установка соединения с бд и сбор конф информации
        # echo=True - ведение лога, poll_recycle=7200 - переустановка соединения с бд каждые 2 часа
        self.engine = create_engine('sqlite:///client_data.db3', echo=True, pool_recycle=7200)
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

    def get_user_contacts(self):
        """Метод класса возвращает список контактов пользователя"""
        return [user[0] for user in self.session.query(self.UserContacts.contact_login).all()]

    def get_users(self):
        """Метод класса возращает список известных пользователей"""
        return [user[0] for user in self.session.query(self.FamousUsers.login).all()]

    def checker_contact(self, contact_login):
        """Метод класса проверяет есть ли контакт в контактах"""
        if self.session.query(self.UserContacts).filter_by(contact_login=contact_login).count():
            return True
        else:
            return False

    def get_history_messages(self, from_who=None, for_who=None):
        """Метод класса возращает историю сообщений"""
        history = self.session.query(self.HistoryMessages)
        if for_who:
            history = history.filter_by(for_user=for_who)
        if from_who:
            history = history.filter_by(from_user=from_who)
        return [(history_line.from_user, history_line.for_user, history_line.message, history_line.date)
                for history_line in history.all()]


if __name__ == '__main__':
    client_storage = ClientStorage()
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
    client_storage.table_clear('all')
