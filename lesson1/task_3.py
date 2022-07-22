def word_byte(word):
    """Возвращает слово в byte"""
    try:
        result = eval("b'{0}'".format(word))
        return result
    except SyntaxError:
        return f'Слово {word} невозможно записать в байтовом типе!'


my_word = word_byte('attribute')
print(my_word)

my_word = word_byte('класс')
print(my_word)

my_word = word_byte('функция')
print(my_word)

my_word = word_byte('type')
print(my_word)
