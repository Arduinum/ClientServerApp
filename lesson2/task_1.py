from encoding_file import encoding_file_detect
import locale
import re
import csv


class MatrixError(Exception):
    def __init__(self, text):
        self.text = text


def get_data(*names):
    """Получает данные об операционных системах из текстовых файлов"""
    main_data, os_prod_list, os_name_list, os_code_list, os_type_list = [[]], [], [], [], []
    main_count = 0
    for name in names:
        encoding = encoding_file_detect(name)
        with open(name, 'r', encoding=encoding) as file:
            file_read = file.read()
            if main_count == 0:
                main_data[0].append(re.search('(Изг.+?)С', file_read).group(0))
                main_data[0].append(re.search('(Наз.+?)С', file_read).group(0))
                main_data[0].append(re.search('(Код.+?)а', file_read).group(0))
                main_data[0].append(re.search('(Тип.+?)ы', file_read).group(0))
                main_count += 1
            os_prod_list.append(re.search('ель ОС:\s*(.+?)\n', file_read).group(1).rstrip())
            os_name_list.append(re.search('ние ОС:\s*(.+?)\n', file_read).group(1).rstrip())
            os_code_list.append(re.search('кта:\s*(.+?)\n', file_read).group(1).rstrip())
            os_type_list.append(re.search('Тип(.)*ы:\s*(.+?)\n', file_read).group(2).rstrip())
    main_data.append(os_prod_list)
    main_data.append(os_name_list)
    main_data.append(os_code_list)
    main_data.append(os_type_list)
    return main_data


def recon_list_csv(data_list):
    """Возращает список в нужном виде для файла с csv форматом"""
    list_recon = [[], [], [], []]
    list_recon[0] = data_list.pop(0)
    for lst in data_list:
        for i, item in enumerate(lst, 1):
            list_recon[i].append(item)

    return list_recon


def write_to_csv(name, data_oc):
    """Записывает данные об операционных системах в файл csv формата"""
    for lst in data_oc:
        if len(lst) != len(data_oc[0]):
            raise MatrixError("Неверная матрица для записи в файл csv формата!")

    default_encoding = locale.getpreferredencoding().lower()
    with open(name, 'w', encoding=default_encoding) as file:
        file_writer = csv.writer(file)
        file_writer.writerows(data_oc)


data = get_data('./lesson2/info_1.txt', './lesson2/info_2.txt', './lesson2/info_3.txt')
data_recon = recon_list_csv(data)
# write_to_csv('./lesson2/data_os.csv', [[0], [0, 1]])  # проверка неправильной матрицы
write_to_csv('./lesson2/data_os.csv', data_recon)
