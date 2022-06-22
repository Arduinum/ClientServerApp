from task_1 import host_ping


class SymbolError(Exception):
    def __str__(self):
        return 'SymbolError'


class LenIpError(Exception):
    def __str__(self):
        return 'LenIpError'


def host_range_ping(table=False):
    """Перебирает ip адреса заданного диапазона"""
    final_oct, ip_end, ip_first = None, None, None
    while True:
        ip_first = input('Введите первый ip для диапазона ip: ')
        try:
            for symbol in ip_first:
                if symbol.isalpha():
                    raise SymbolError
            if len(ip_first.split('.')) != 4:
                raise LenIpError
            final_oct = int(ip_first.split('.')[3])
            break
        except SymbolError as err:
            print(f'{err}, ip адрес {ip_first} имеет в себе буквы!')
        except LenIpError as err:
            print(f'{err}, ip адрес {ip_first} иммет колличество цифр больше либо меньше четырёх!')
    while True:
        ip_end = input('Введите колличество ip адресов для проверки: ')
        if not ip_end.isdigit():
            print('Ввести можно только число!')
        else:
            if (final_oct + int(ip_end)) > 256:
                print(f'Максимальное число хостов {256 - final_oct}')
            else:
                break
    pattern_ip = '.'.join(ip_first.split('.')[0:-1]) + '.'
    hosts = [f'{pattern_ip}{final_oct + num}' for num in range(int(ip_end))]
    host_ping(hosts, table)


if __name__ == '__main__':
    host_range_ping()
