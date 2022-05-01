import locale
from chardet import detect


def create_txt(name, strings):
    """Создаёт текстовый файл в кодировке операционной системы"""
    default_encoding = locale.getpreferredencoding().lower()
    with open(name, 'w', encoding=default_encoding) as file:
        file.write(strings)


def encoding_detect(name):
    """Определяет кодировку текстового файла"""
    with open(name, 'rb') as file:
        content = file.read()
        return detect(content)['encoding']


def read_txt(name, encoding):
    """Открывает текстовый файл в режиме чтение"""
    with open(name, 'r', encoding=encoding) as file:
        return file.read()


create_txt('test_file.txt', 'сетевое программирование\nсокет\nдекоратор')
encode_file = encoding_detect('test_file.txt')
file_read = read_txt('test_file.txt', encode_file)
print(file_read)
