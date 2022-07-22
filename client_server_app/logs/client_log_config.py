from sys import path as sys_path
sys_path.append('../')
from logging import getLogger, Formatter, StreamHandler, FileHandler, DEBUG
from os.path import abspath, dirname

logger = getLogger('client')

# объект для форматирования строки
format_message = Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# обработчик для логирования в файл
path_file = f'{dirname(abspath(__file__))}/client.log'
file_hand = FileHandler(path_file, encoding='utf-8')
file_hand.setLevel(DEBUG)
file_hand.setFormatter(format_message)

# добавили в логгер новый обработчик событий и установили уровень логирования
logger.addHandler(file_hand)
logger.setLevel(DEBUG)

if __name__ == '__main__':
    # тестовый запуск - вывод данных в консоль, которые логгер должен выдать в файл
    terminal = StreamHandler()
    terminal.setLevel(DEBUG)
    terminal.setFormatter(format_message)
    logger.addHandler(terminal)
    logger.setLevel(DEBUG)
    logger.debug('test debug')
    logger.info('test info')
    logger.warning('test warning')
    logger.error('test error')
    logger.critical('test critical')
