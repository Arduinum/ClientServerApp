from chardet import detect


def encoding_file_detect(name):
    """Определяет кодировку для файла"""
    with open(name, 'rb') as file:
        content = file.read()
        return detect(content)['encoding']
