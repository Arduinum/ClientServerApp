import json
from dotenv import load_dotenv
from os import getenv


load_dotenv()


def get_message(client):
    """Принимает и декодирует сообщение"""
    encode_response = client.recv(int(getenv('MAX_MESSAGE_LEN_BYTE')))
    if str(type(encode_response)) == "<class 'bytes'>":
        json_response = encode_response.decode(getenv('ENCODING'))
        if str(type(json_response)) == "<class 'str'>":
            response = json.loads(json_response)
            if str(type(response)) == "<class 'dict'>":
                return response
            raise ValueError
        raise ValueError
    raise ValueError


def send_message(socket, message):
    """Кодирует и отправляет сообщение"""
    if str(type(message)) != "<class 'dict'>":
        raise ValueError
    json_message = json.dumps(message)
    encode_message = json_message.encode(getenv('ENCODING'))
    socket.send(encode_message)
