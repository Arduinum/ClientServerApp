import json
from yaml import load, FullLoader
from time import ctime
from inspect import stack
from logging import getLogger
from logs import server_log_config, client_log_config


# def log(func):
#     def wrapper(*args, **kwargs):
#         func_call = func(*args, **kwargs)
#         logger_now = None
#         date = ctime()
#         call_from = stack()[1][3]
#         if call_from == 'work_client' or call_from == 'get_answer' or call_from == 'data_connect_serv' or \
#                 call_from == 'interactive_for_user' or call_from == 'message_server_from_user' or \
#                 call_from == 'run':
#             logger_now = getLogger('client')
#         if call_from == 'work_server' or call_from == 'message_handler':
#             logger_now = getLogger('server')
#         logger_now.debug(f'{date} - функция {func.__name__} вызвана из функции {call_from}')
#         return func_call
#     return wrapper


def log_client(func):
    def wrapper(*args, **kwargs):
        func_call = func(*args, **kwargs)
        date = ctime()
        call_from = stack()[1][3]
        logger_now = getLogger('client')
        logger_now.debug(f'{date} - функция {func.__name__} вызвана из функции {call_from}')
        return func_call
    return wrapper


def log_server(func):
    def wrapper(*args, **kwargs):
        func_call = func(*args, **kwargs)
        date = ctime()
        call_from = stack()[1][3]
        logger_now = getLogger('server')
        logger_now.debug(f'{date} - функция {func.__name__} вызвана из функции {call_from}')
        return func_call
    return wrapper


def read_conf(file_name):
    """Читает конфигурационный файл в формате yaml"""
    with open(file_name, 'r', encoding='utf-8') as conf:
        return load(conf, Loader=FullLoader)


name = './common/config.yaml'


def get_message(client, conf_name=name):
    """Принимает и декодирует сообщение"""
    conf = read_conf(conf_name)
    encode_response = client.recv(conf['MAX_MESSAGE_LEN_BYTE'])
    if str(type(encode_response)) == "<class 'bytes'>":
        if encode_response == b'':
            return None
        json_response = encode_response.decode(conf['ENCODING'])
        if str(type(json_response)) == "<class 'str'>":
            response = json.loads(json_response)
            if str(type(response)) == "<class 'dict'>":
                return response
            raise ValueError
        raise ValueError
    raise ValueError


def send_message(socket, message, conf_name=name):
    """Кодирует и отправляет сообщение"""
    conf = read_conf(conf_name)
    if str(type(message)) != "<class 'dict'>":
        raise ValueError
    json_message = json.dumps(message)
    encode_message = json_message.encode(conf['ENCODING'])
    socket.send(encode_message)
