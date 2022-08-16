from json import loads, dumps
from yaml import load, FullLoader
from logging import getLogger
from logs import server_log_config, client_log_config
from common.config_path_file import CONFIG_PATH
from sys import argv
from re import search


logger = None
module = argv[0].split('/')[-1]

if 'server' in module:
    logger = getLogger('server')
elif 'client' in module:
    logger = getLogger('client')


def read_conf(file_name):
    """Читает конфигурационный файл в формате yaml"""
    with open(file_name, 'r', encoding='utf-8') as config:
        return load(config, Loader=FullLoader)


def read_conf_lines(file_name):
    """Читает конфегурационный файл и возвращает его в виде списка строк"""
    with open(file_name, 'r', encoding='utf-8') as config:
        return config.readlines()


def replace_value_list_conf(conf_list, key, value):
    """Функция для замены значения ключа кофига. Работает со списком строк (в каждой строке ключ и значение)"""
    for line in conf_list:
        if ':' in line:
            key_value = line.split(':')
            if key_value[0] == key:
                key_value[1] = value + '\n'
                conf_list[conf_list.index(line)] = ': '.join(key_value)
                return conf_list


conf = read_conf(CONFIG_PATH)


def check_gui_argv():
    """Функция для проверки аргумента нужен ли gui при запуске сервера"""
    if '--no_gui' in argv:
        return True
    return False


def check_addr_argv():
    """Функция для проверки аргумента адреса на предмет наличия"""
    try:
        if '-a' in argv:
            return argv[argv.index('-a') + 1]
        elif '--addr' in argv:
            return argv[argv.index('-addr') + 1]
        else:
            return conf['ADDR_DEF']
    except IndexError:
        return conf['ADDR_DEF']


def check_name_argv():
    """Функция для проверки аргумента имени на предмет наличия"""
    logger.debug('Проверка аргумента имени')
    try:
        if '-n' in argv:
            return argv[argv.index('-n') + 1]
        elif '--name' in argv:
            return argv[argv.index('--name') + 1]
        else:
            return None
    except IndexError:
        return None


def check_port_argv():
    """Функция для проверки аргумента порта на предмет наличия """
    logger.debug('Проверка аргумента порта')
    try:
        if '--port' in argv:
            return argv[argv.index('--port') + 1]
        else:
            return conf['PORT_DEF']
    except IndexError:
        return conf['PORT_DEF']


def check_passwd_argv():
    """Функция для проверки аргумента пароля"""
    logger.debug('Проверка аргумента пароля')
    try:
        if '--password' in argv:
            return argv[argv.index('--password') + 1]
        elif '--passwd' in argv:
            return argv[argv.index('--passwd') + 1]
        elif '-p' in argv:
            return argv[argv.index('-p') + 1]
        else:
            return None
    except IndexError:
        return None


def get_message(client):
    """Принимает и декодирует сообщение"""
    encode_response = client.recv(conf['MAX_MESSAGE_LEN_BYTE'])
    if str(type(encode_response)) == "<class 'bytes'>":
        if encode_response == b'':
            return None
        json_response = encode_response.decode(conf['ENCODING'])
        if str(type(json_response)) == "<class 'str'>":
            response = loads(json_response)
            if str(type(response)) == "<class 'dict'>":
                return response
            raise ValueError
        raise ValueError
    raise ValueError


def send_message(sock, message):
    """Кодирует и отправляет сообщение"""
    if str(type(message)) != "<class 'dict'>":
        raise ValueError
    json_message = dumps(message)
    encode_message = json_message.encode(conf['ENCODING'])
    sock.send(encode_message)
