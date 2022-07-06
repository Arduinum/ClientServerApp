def encoder(*words):
    """Преобразует слова из строкового в байтовое представление и возвращает их в виде списка"""
    list_result = []
    for word_str in words:
        list_result.append(word_str.encode('utf-8'))
    return list_result


def decoder(words):
    """Преобразует слова из байтового представления в строки и возвращает их в виде списка"""
    list_result = []
    for word_byte in words:
        list_result.append(word_byte.decode('utf-8'))
    return list_result


words_byte = encoder('разработка', 'администрирование', 'protocol', 'standard')

for word in words_byte:
    print(word, type(word))

print('\n')

words_str = decoder(words_byte)

for word in words_str:
    print(word, type(word))
