import yaml
from encoding_file import encoding_file_detect


my_dict = {
    'list_data': [1, 2, '3', '4'],
    'num_data': 62,
    'dict_data': {251: '√', 252: '№'}
}


def write_data_to_yaml(name_yaml, data):
    """Записывает данные в файл формата yaml"""
    with open(name_yaml, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=True, allow_unicode=True)


def read_yaml(name_yaml):
    """Читает файл формата yaml"""
    encoding = encoding_file_detect(name_yaml)
    with open(name_yaml, 'r', encoding=encoding) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def origin_check(name_yaml, data_yaml, initial_data):
    """Сравнивает записанный yaml с оригинальными данными"""
    if data_yaml == initial_data:
        return f'Данные файла {name_yaml} совпадают с исходными данными'
    else:
        return f'Данные файла {name_yaml} не совпадают с исходными данными!'


write_data_to_yaml('./lesson2/file.yaml', my_dict)
file_read = read_yaml('./lesson2/file.yaml')
file_check = origin_check('./lesson2/file.yaml', file_read, my_dict)
print(file_check)
file_check = origin_check('./lesson2/file.yaml', file_read, {2: '2'})  # проверка несовпадающих данных
print(file_check)
