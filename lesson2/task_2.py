import json


def write_order_to_json(item, quantity, price, buyer, date):
    """Записывает данные о покупке товара в файл формата json"""
    dict_write = dict()
    dict_write['item'], dict_write['quantity'], dict_write['price'], dict_write['buyer'], dict_write['date'] = item, \
        quantity, price, buyer, date
    file_read = open('./lesson2/orders.json', 'r', encoding='utf-8')
    json_load = json.load(file_read)
    with open('./lesson2/orders.json', 'w', encoding='utf-8') as file_write:
        json_load['orders'].append(dict_write)
        print(json_load)
        json.dump(json_load, file_write, indent=4, sort_keys=True, ensure_ascii=False)


write_order_to_json('Arduino Mega 2560 R3', 2, 15510, 'Антон Фадеев', '01.05.2022')
