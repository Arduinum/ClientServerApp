#!../venv/bin/python3
import signal
from os import path, setpgrp, killpg
from sys import executable
from time import sleep
from subprocess import Popen


PY_PATH = executable  # путь до интерпритатора python
ROOT_PATH = path.dirname(path.abspath(__file__))  # путь до корневого каталога проекта


def get_subproc(str_args):
    """Функция запускает терминал с программой в ubuntu подобных OS"""
    sleep(0.1)  # задержка 0.1 сек
    file_path = f'{PY_PATH} {ROOT_PATH}/{str_args}'  # путь до файла
    args = ['gnome-terminal', '--disable-factory', '--', 'bash', '-c', file_path]  # аргументы для запуска
    return Popen(args, preexec_fn=setpgrp)


def launcher():
    """Функция для удобного запуска сервера и клиентов"""
    process = list()
    while True:
        command = input('Команды: exit - выйти, start - запуск сервера и клиентов, close - закрыть все окна: ')

        if command == 'exit':
            break
        elif command == 'start':
            process.append(get_subproc('server.py'))

            for i in range(2):
                process.append(get_subproc(f'client.py -n client{i + 1}'))

        elif command == 'close':
            while len(process) > 0:
                kill_proc = process.pop()
                killpg(kill_proc.pid, signal.SIGINT)  # убиваем все процессы


# launcher()


if __name__ == '__main__':
    launcher()
