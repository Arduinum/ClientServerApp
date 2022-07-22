from tabulate import tabulate
from task_2 import host_range_ping
from task_1 import nodes


def host_range_ping_tab(nodes_list):
    """Показывает доступные и недоступные ip адреса в виде таблицы"""
    host_range_ping(table=True)
    table_ip = tabulate(nodes_list, headers='keys', tablefmt='grid', stralign='center')
    return table_ip


if __name__ == '__main__':
    table = host_range_ping_tab(nodes)
    print(table)
