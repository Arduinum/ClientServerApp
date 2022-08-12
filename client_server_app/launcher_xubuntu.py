#!../venv/bin/python3
import signal
from os import path, setpgrp, killpg
from sys import executable
from time import sleep
from subprocess import Popen


class Launcher:
    def __init__(self):
        self.PY_PATH = executable  # путь до интерпритатора python
        self.ROOT_PATH = path.dirname(path.abspath(__file__))  # путь до корневого каталога проекта
        self.process = list()

    def get_subproc(self, str_args):
        """Метод класса запускает терминал с программой в ubuntu подобных OS"""
        sleep(0.1)  # задержка 0.1 сек
        file_path = f'{self.PY_PATH} {self.ROOT_PATH}/{str_args}'  # путь до файла
        args = ['gnome-terminal', '--disable-factory', '--', 'bash', '-c', file_path]  # аргументы для запуска
        return Popen(args, preexec_fn=setpgrp)

    def main(self):
        """Метод класса для удобного запуска сервера и клиентов"""
        while True:
            command = input('Команды: exit - выйти, '
                            'server - запуск сервера, '
                            'client - запуск клиента/клиентов, '
                            'close - закрыть все окна: ')

            if command == 'exit':
                break
            elif command == 'server':
                self.process.append(self.get_subproc('server.py'))
            elif command == 'client':
                count_client = None
                while True:
                    try:
                        count_client = int(input('Введите колличество клиентов: '))
                    except ValueError as err:
                        print(f'{err}.\nКолличество клиентов может быть только числом!')
                    else:
                        for i in range(count_client):
                            self.process.append(self.get_subproc('client.py'))
                        break
            elif command == 'close':
                while len(self.process) > 0:
                    kill_proc = self.process.pop()
                    killpg(kill_proc.pid, signal.SIGINT)  # убиваем все процессы
            else:
                print(f'Команда - {command} не существует!')


# launcher = Launcher()
# launcher.main()


if __name__ == '__main__':
    launcher = Launcher()
    launcher.main()
