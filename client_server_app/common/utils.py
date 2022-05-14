import json
from yaml import load, FullLoader


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
