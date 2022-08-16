from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from common.utils import read_conf
from os.path import dirname, realpath
from common.config_path_file import CONFIG_PATH


class ServerStorage:
    """Класс для работы с базой данных сервера в декларативном стиле"""
    Base = declarative_base()

    class AllUsers(Base):
        """Класс для создания таблицы"""
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        hash_passwd = Column(String)
        publickey = Column(Text)
        last_entry_time = Column(DateTime)

        def __init__(self, login, hash_passwd):
            self.login = login
            self.hash_passwd = hash_passwd
            self.publickey = None
            self.last_entry_time = datetime.now()
            super().__init__()

    class ActiveUsers(Base):
        """Класс для создания таблицы"""
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        login_id = Column(Integer, ForeignKey('all_users.id'), unique=True)
        entry_time = Column(DateTime)
        ip_address = Column(String)
        port = Column(Integer)

        def __init__(self, login_id, entry_time, ip_address, port):
            self.login_id = login_id
            self.entry_time = entry_time
            self.ip_address = ip_address
            self.port = port
            super().__init__()

    class HistoryLogins(Base):
        """Класс для создания таблицы"""
        __tablename__ = 'history_logins'
        id = Column(Integer, primary_key=True)
        login_id = Column(Integer, ForeignKey('all_users.id'))
        entry_time = Column(DateTime)
        ip_address = Column(String)
        port = Column(Integer)

        def __init__(self, login_id, entry_time, ip_address, port):
            self.login_id = login_id
            self.entry_time = entry_time
            self.ip_address = ip_address
            self.port = port
            super().__init__()

    class UsersContacts(Base):
        """Класс контакты пользователей"""
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        login_id = Column(ForeignKey('all_users.id'))
        contact_login_id = Column(ForeignKey('all_users.id'))

        def __init__(self, login_id, contact_login_id):
            self.login_id = login_id
            self.contact_login_id = contact_login_id
            super().__init__()

    class UsersHistory(Base):
        """Класс история действий пользователей"""
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        login_id = Column(ForeignKey('all_users.id'))
        transmitted = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, login_id):
            self.login_id = login_id
            self.transmitted = 0  # переданных сообщений
            self.accepted = 0  # полученных сообщений
            super().__init__()

    def __init__(self, path=None, name_db=None):
        # установка соединения с бд и сбор конф информации
        # echo=True - ведение лога, poll_recycle=7200 - переустановка соединения с бд каждые 2 часа
        self.conf = read_conf(CONFIG_PATH)
        if not name_db:
            name_db = self.conf['DB_NAME_FILE']
        if not path:
            path = self.conf['DB_PATH']
        self.engine = create_engine(f'sqlite:///{path}/{name_db}?check_same_thread=False', echo=True, pool_recycle=7200)
        self.Base.metadata.create_all(self.engine)  # создаём все таблицы
        session_fabric = sessionmaker(bind=self.engine)
        self.session = session_fabric()  # создаём сессию

    def user_login(self, login, ip_address, port, pub_key):
        """Метод класса для фиксации входа пользователя"""
        try:
            user_search = self.session.query(self.AllUsers).filter_by(login=login)  # ищим логин
            user = None
            # если находим, то обновляем время входа
            if user_search.count():
                user = user_search.first()
                user.last_entry_time = datetime.now()
                if user.publickey != pub_key:
                    user.publickey = pub_key
            elif not user_search.count():
                raise ValueError('Пользователь не был зарегистрирован!')

            user_active = self.ActiveUsers(user.id, datetime.now(), ip_address, port)
            self.session.add(user_active)

            history_logins = self.HistoryLogins(user.id, datetime.now(), ip_address, port)
            self.session.add(history_logins)
            self.session.commit()
        except Exception as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def user_logout(self, login):
        """Метод класса, который действует при разлогировании клиента"""
        try:
            user = self.session.query(self.AllUsers).filter_by(login=login).first()
            self.session.query(self.ActiveUsers).filter_by(login_id=user.id).delete()  # ищим логин
            self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def get_list_data(self, command, login=None):
        """Метод для получения данных из таблиц в виде списка"""
        try:
            if command == 'users':
                users_reg = self.session.query(self.AllUsers.login, self.AllUsers.last_entry_time)
                return users_reg.all()
            elif command == 'active_users':
                act_users = self.session.query(
                    self.AllUsers.login,
                    self.ActiveUsers.ip_address,
                    self.ActiveUsers.port,
                    self.ActiveUsers.entry_time).join(self.AllUsers)
                return act_users.all()
            elif command == 'history':
                history_users = self.session.query(
                    self.AllUsers.login,
                    self.HistoryLogins.ip_address,
                    self.HistoryLogins.port,
                    self.HistoryLogins.entry_time).join(self.AllUsers)
                if login:
                    history_users = history_users.filter(self.AllUsers.login == login)
                return history_users.all()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def table_clear(self, command):
        """Метод класса для очищения таблиц от данных"""
        try:
            if command == 'all':
                self.session.query(self.AllUsers).delete()
                self.session.query(self.ActiveUsers).delete()
                self.session.query(self.HistoryLogins).delete()
                self.session.query(self.UsersContacts).delete()
                self.session.query(self.UsersHistory).delete()
                self.session.commit()
            else:
                eval(f'self.session.query(self.{command}).delete()')
                self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def working_message(self, addresser, receiver):
        """Метод класса для фиксации передачи сообщения и делает об этом отметки в бд"""
        try:
            addresser = self.session.query(self.AllUsers).filter_by(login=addresser).first().id  # отправитель сообщения
            receiver = self.session.query(self.AllUsers).filter_by(login=receiver).first().id  # получатель сообщения
            addresser_line = self.session.query(self.UsersHistory).filter_by(login_id=addresser).first()
            addresser_line.transmitted += 1
            receiver_line = self.session.query(self.UsersHistory).filter_by(login_id=receiver).first()
            receiver_line.accepted += 1
            self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def add_contact(self, login, contact_user):
        """Метод класса для добавления контакта из бд"""
        try:
            user = self.session.query(self.AllUsers).filter_by(login=login).first()
            contact_user = self.session.query(self.AllUsers).filter_by(login=contact_user).first()

            if not contact_user:
                return
            if self.session.query(self.UsersContacts).filter_by(
                    login_id=user.id, contact_login_id=contact_user.id).count():
                return

            contact_line = self.UsersContacts(user.id, contact_user.id)
            self.session.add(contact_line)
            self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def delete_contact(self, login, contact_user):
        """Метод класса для удаления контакта из бд"""
        try:
            user = self.session.query(self.AllUsers).filter_by(login=login).first()
            contact_user = self.session.query(self.AllUsers).filter_by(login=contact_user).first()

            if not contact_user:
                return

            self.session.query(self.UsersContacts).filter(
                self.UsersContacts.login_id == user.id,
                self.UsersContacts.contact_login_id == contact_user.id
            ).delete()
            self.session.commit()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def delete_user(self, login):
        """Метод класса для удаления пользователя из бд"""
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(login_id=user.id).delete()
        self.session.query(self.HistoryLogins).filter_by(login_id=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(login_id=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(contact_login_id=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(login_id=user.id).delete()
        self.session.query(self.AllUsers).filter_by(login=login).delete()
        self.session.commit()

    def get_users_contacts(self, login):
        """Метод класса возвращающий список контактов пользователя"""
        try:
            user = self.session.query(self.AllUsers).filter_by(login=login).one()
            users_contacts = self.session.query(self.UsersContacts, self.AllUsers.id). \
                filter_by(login_id=user.id).join(self.AllUsers, self.UsersContacts.contact_login_id == self.AllUsers.id)
            return [contact_user[1] for contact_user in users_contacts.all()]
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def get_message_count(self):
        """Метод класса возвращающий колличество переданных и полученных сообщений"""
        try:
            message_count = self.session.query(
                self.AllUsers.login,
                self.AllUsers.last_entry_time,
                self.UsersHistory.transmitted,
                self.UsersHistory.accepted
            ).join(self.AllUsers)
            return message_count.all()
        except (Exception, ) as err:
            print(f'Ошибка - {err} при работе с данными таблицы!')

    def checker_user(self, login):
        """Метод класса проверяет существует ли пользователь"""
        if self.session.query(self.AllUsers).filter_by(login=login).count():
            return True
        else:
            return False

    def register_user(self, login, hash_passwd):
        """Метод класса для регистрации пользователя и создания в записи в таблице статистики"""
        user_line = self.AllUsers(login, hash_passwd)
        self.session.add(user_line)
        self.session.commit()
        history_line = self.UsersHistory(user_line.id)
        self.session.add(history_line)
        self.session.commit()

    def get_pub_key(self, login):
        """Метод класса для получения публичного ключа пользователя"""
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        return user.publickey

    def get_hash(self, login):
        """Метод класса для получения хэша пароля пользователя."""
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        return user.hash_passwd


if __name__ == '__main__':
    dir_path = dirname(realpath(__file__))
    storage = ServerStorage(dir_path)
    storage.table_clear('all')
    # storage.table_clear('AllUsers')
    # storage.user_login('Bot228', '0.0.0.0', 7777)
    # storage.user_login('BotT1000', '0.0.0.1', 7777)
    # storage.user_logout('Bot228')
    # storage.user_logout('BotT1000')
    # storage.user_login('BotT1000', '0.0.0.1', 7777)
    # users = storage.get_list_data('users')
    # print(users)
    # active_users = storage.get_list_data('active_users')
    # print(active_users)
    # history = storage.get_list_data('history')
    # print(history)
    # history = storage.get_list_data('history', 'BotT1000')
    # print(history)
    # storage.working_message('Bot228', 'BotT1000')
    # storage.add_contact('BotT1000', 'BotT1000')
    # storage.add_contact('Bot228', 'Bot228')
    # storage.delete_contact('BotT1000', 'BotT1000')
    # print(storage.get_users_contacts('Bot228'))
    # print(storage.get_message_count())
