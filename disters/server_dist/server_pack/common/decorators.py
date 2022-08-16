from sys import argv, path as sys_path
sys_path.append('../')
from common.utils import read_conf
from socket import socket
from time import ctime
from inspect import stack
from logging import getLogger
from logs import server_log_config, client_log_config
from common.config_path_file import CONFIG_PATH


logger = None
module = argv[0].split('/')[-1]
conf = read_conf(CONFIG_PATH)

if 'server' in module:
    logger = getLogger('server')
elif 'client' in module:
    logger = getLogger('client')


def log(func):
    """Функция логирования"""

    def wrapper(*args, **kwargs):
        func_call = func(*args, **kwargs)
        date = ctime()
        call_from = stack()[1][3]
        logger.debug(f'{date} - функция {func.__name__} вызвана из функции {call_from} из модуля {func.__module__}')
        return func_call

    return wrapper


def login_needed(func):
    """Функция декоратор, проверяющая, что клиент авторизован на сервере"""
    def check(*args, **kwargs):
        from server_pack.kernel import MessageReceiver
        if isinstance(args[0], MessageReceiver):
            found = False
            for arg in args:
                if isinstance(arg, socket):
                    for client in args[0].client_names:
                        if args[0].client_names[client] == arg:
                            found = True
            # Если presence сообщение, то разрешено
            for arg in args:
                if isinstance(arg, dict):
                    if conf['ACTION'] in arg and arg[conf['ACTION']] == conf['PRESENCE']:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)
    return check
