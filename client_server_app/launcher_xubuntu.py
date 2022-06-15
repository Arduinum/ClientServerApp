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
            command = input('Команды: exit - выйти, start - запуск сервера и клиентов, close - закрыть все окна: ')

            if command == 'exit':
                break
            elif command == 'start':
                self.process.append(self.get_subproc('server.py'))

                for i in range(2):
                    self.process.append(self.get_subproc(f'client.py -n client{i + 1}'))

            elif command == 'close':
                while len(self.process) > 0:
                    kill_proc = self.process.pop()
                    killpg(kill_proc.pid, signal.SIGINT)  # убиваем все процессы


# launcher = Launcher()
# launcher.main()


if __name__ == '__main__':
    launcher = Launcher()
    launcher.main()
