#!../venv/bin/python3
import signal
from os import path, setpgrp, killpg
from sys import executable
from time import sleep
from subprocess import Popen


PY_PATH = executable  # путь до интерпритатора python
ROOT_PATH = path.dirname(path.abspath(__file__))  # путь до корневого каталога проекта
MAX_CLIENTS_COUNT = 5  # максимальное количество клиентов


class ClientCountError(Exception):
    def __str__(self):
        return 'Ошибка ClientCountError'


def get_subproc(str_args):
    """Функция запускает терминал с программой в ubuntu подобных OS"""
    sleep(0.1)  # задержка 0.1 сек
    file_path = f'{PY_PATH} {ROOT_PATH}/{str_args}'  # путь до файла
    args = ['gnome-terminal', '--disable-factory', '--', 'bash', '-c', file_path]  # аргументы для запуска
    return Popen(args, preexec_fn=setpgrp)


def input_count(action):
    """Функция для ввода колличества клиентов"""
    if action == 'send':
        action = 'отправляющих'
    if action == 'listen':
        action = 'принимающих'
    return abs(int(input(f'Введите колличество клиентов, {action} сообщение: ')))


def launcher():
    """Функция для удобного запуска сервера и клиентов"""
    process = list()
    while True:
        command = input('Команды: exit - выйти, start - запуск сервера и клиентов, close - закрыть все окна: ')

        if command == 'exit':
            break
        elif command == 'start':
            process.append(get_subproc('server.py'))

            s_client_count = None
            l_client_count = None
            while True:
                try:
                    if s_client_count is None:
                        s_client_count = input_count('send')
                    elif s_client_count > MAX_CLIENTS_COUNT:
                        s_client_count = input_count('send')

                    if l_client_count is None:
                        l_client_count = input_count('listen')
                    elif l_client_count > MAX_CLIENTS_COUNT:
                        l_client_count = input_count('listen')

                    if s_client_count > MAX_CLIENTS_COUNT or l_client_count > MAX_CLIENTS_COUNT:
                        raise ClientCountError
                except ClientCountError as err:
                    print(f'{err}, максимальное число клиентов {MAX_CLIENTS_COUNT}!')
                except ValueError as err:
                    print(f'{err}, вы должны ввести число!')
                if s_client_count <= MAX_CLIENTS_COUNT and l_client_count <= MAX_CLIENTS_COUNT:
                    break

            for _ in range(s_client_count):
                process.append(get_subproc('client.py -m send'))

            for _ in range(l_client_count):
                process.append(get_subproc('client.py -m listen'))

        elif command == 'close':
            while len(process) > 0:
                kill_proc = process.pop()
                killpg(kill_proc.pid, signal.SIGINT)  # убиваем все процессы


launcher()


# if __name__ == '__main__':
#     launcher()
