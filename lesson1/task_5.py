import chardet
import subprocess
import platform
import locale


def ping_site(site):
    """Выдаёт пинг для сайта в нужной для системы кодировке"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, '2', site]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    default_encoding = locale.getpreferredencoding().lower()
    for line in process.stdout:
        result = chardet.detect(line)
        line = line.decode(result['encoding']).encode(default_encoding)
        yield line.decode(default_encoding)


for ping in ping_site('yandex.ru'):
    print(ping)

for ping in ping_site('youtube.com'):
    print(ping)
