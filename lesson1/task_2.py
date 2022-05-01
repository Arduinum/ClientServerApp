def word_bytes(*words):
    """Возвращает список слов byte"""
    list_bytes = []

    for word in words:
        list_bytes.append(eval("b'{0}'".format(word)))
    return list_bytes


lst_bytes = word_bytes('class', 'function', 'method')

for wrd in lst_bytes:
    print(wrd, type(wrd), len(wrd))
