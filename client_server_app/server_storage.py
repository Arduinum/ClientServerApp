from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


class ServerStorage:
    """Класс для работы с базой данных сервера в декларативном стиле"""
    Base = declarative_base()

    class AllUsers(Base):
        """Класс для создания таблицы"""
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_entry_time = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_entry_time = datetime.now()

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

    def __init__(self):
        # установка соединения с бд и сбор конф информации
        # echo=True - ведение лога, poll_recycle=7200 - переустановка соединения с бд каждые 2 часа
        self.engine = create_engine('sqlite:///sever_data.db3', echo=True, pool_recycle=7200)
        self.Base.metadata.create_all(self.engine)  # создаём все таблицы
        session_fabric = sessionmaker(bind=self.engine)
        self.session = session_fabric()  # создаём сессию

    def user_login(self, login, ip_address, port):
        """Метод класса для фиксации входа пользователя"""
        try:
            user_search = self.session.query(self.AllUsers).filter_by(login=login)  # ищим логин
            # если находим, то обновляем время входа
            if user_search.count():
                user = user_search.first()
                user.last_entry_time = datetime.now()
                self.session.commit()
            # если не находим создаём новго пользователя
            else:
                user = self.AllUsers(login)
                self.session.add(user)
                self.session.commit()

            user_active = self.ActiveUsers(user.id, datetime.now(), ip_address, port)
            self.session.add(user_active)

            history_logins = self.HistoryLogins(user.id, datetime.now(), ip_address, port)
            self.session.add(history_logins)
            self.session.commit()
        except (Exception, ) as err:
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
        if command == 'all':
            self.session.query(self.AllUsers).delete()
            self.session.query(self.ActiveUsers).delete()
            self.session.query(self.HistoryLogins).delete()
            self.session.commit()
        else:
            eval(f'self.session.query(self.{command}).delete()')
            self.session.commit()


if __name__ == '__main__':
    storage = ServerStorage()
    # storage.table_clear('all')
    # storage.table_clear('AllUsers')
    storage.user_login('Bot228', '0.0.0.0', 7777)
    storage.user_login('BotT1000', '0.0.0.1', 7777)
    storage.user_logout('Bot228')
    storage.user_logout('BotT1000')
    storage.user_login('BotT1000', '0.0.0.1', 7777)
    users = storage.get_list_data('users')
    print(users)
    active_users = storage.get_list_data('active_users')
    print(active_users)
    history = storage.get_list_data('history')
    print(history)
    history = storage.get_list_data('history', 'BotT1000')
    print(history)
