from logging import getLogger, Formatter, StreamHandler, handlers, FileHandler, DEBUG
from os import path
from time import strftime


logger = getLogger('server')

# объект для форматирования строки
format_message = Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# обработчик для логирования в файл
file_hand = handlers.TimedRotatingFileHandler(
    path.abspath('server.log'), 'D', 1, encoding='utf-8')  # ротация логов каждый день
file_hand.setLevel(DEBUG)
file_hand.setFormatter(format_message)

# добавили в логгер новый обработчик событий и установили уровень логирования
logger.addHandler(file_hand)
logger.setLevel(DEBUG)

date = f"{strftime('%y')}-{strftime('%m')}-{strftime('%d')}"
file_hand_one_day = FileHandler(path.abspath(f'server.log.{date}'))
file_hand_one_day.setLevel(DEBUG)
file_hand_one_day.setFormatter(format_message)
logger.addHandler(file_hand_one_day)
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
