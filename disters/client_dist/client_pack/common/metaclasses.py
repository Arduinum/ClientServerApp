from dis import get_instructions


class ServerVerifier(type):
    def __init__(cls, meta_name, bases_classes, meta_dict):
        methods_glob = list()

        for key in meta_dict.keys():
            try:
                iterator = get_instructions(meta_dict[key])
            except (TypeError, SyntaxError):
                pass
            # разбор данных что в итераторе
            else:
                for item in iterator:
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods_glob:
                            methods_glob.append(item.argval)  # SOCK_STREAM и AF_INET у меня в LOAD_GLOBAL

        if 'connect' in methods_glob:
            raise TypeError('Метод connect не может быть использован в классе сервер')
        if not ('SOCK_STREAM' in methods_glob and 'AF_INET' in methods_glob):
            raise TypeError('Сокет был неправильно инициализирован!')
        super().__init__(meta_name, bases_classes, meta_dict)


class ClientVerifier(type):
    def __init__(cls, meta_name, bases_classes, meta_dict):
        methods_glob = list()

        for key in meta_dict.keys():
            try:
                iterator = get_instructions(meta_dict[key])
            except (TypeError, SyntaxError):
                pass
            # разбор данных что в итераторе
            else:
                for item in iterator:
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods_glob:
                            methods_glob.append(item.argval)

        if 'accept' in methods_glob or 'listen' in methods_glob:
            raise TypeError('В классе используется запрещённый метод!')
        if 'get_message' in methods_glob or 'send_message' in methods_glob:
            pass
        else:
            raise TypeError('Отсутствует вызовы функций для работы с сокетами!')
        super().__init__(meta_name, bases_classes, meta_dict)
