from threading import Thread
from subprocess import Popen, PIPE
from ipaddress import ip_address
from pprint import pprint
from platform import system
from time import time


nodes = {'Доступные': list(), 'Недоступные': list()}


def ping(node, nodes_dir, table=False):
    """Функция для пингования узла"""
    param = '-n' if system() == 'Windows' else '-c'
    answer = Popen(['ping', param, '1', '-w', '1', str(node)], stdout=PIPE)

    if answer.wait() == 0:
        nodes_dir['Доступные'].append(str(node))
        if not table:
            print(f'Узел {node} доступен')
    else:
        nodes_dir['Недоступные'].append(str(node))
        if not table:
            print(f'Узел {node} недоступен')


def host_ping(addr_list, table=False):
    """Проверяет доступность сетевых узлов"""
    print('Старт проверки доступности сетевых узлов.')
    processes = []

    for addr in addr_list:
        try:
            node = ip_address(addr)
            if not table:
                print(f'ipv4 - {node}')
        except ValueError:
            node = addr
            if not table:
                print(f'domain name - {node}')

        ping_proc = Thread(target=ping, args=(node, nodes, table))
        ping_proc.daemon = True
        ping_proc.start()
        processes.append(ping_proc)

    for proc in processes:
        proc.join()  # ожидает завершения потока


if __name__ == '__main__':
    nodes_list = [
        '8.8.8.0', 'google.com', '8.8.8.1', '8.8.8.2', '8.8.8.3', '8.8.8.4', '8.8.8.5', 'www.arduino.cc', '8.8.8.6',
        '8.8.8.7', '8.8.8.8'
    ]
    start = time()
    host_ping(nodes_list)
    end = time()
    print(f'Время выполнения - {"%.2f" % (end - start)} сек')
    pprint(nodes)
