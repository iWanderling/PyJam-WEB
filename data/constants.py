from random import choice
import string


def identifier():
    """ Создаёт уникальное имя для файла, который нужно распознать.
        Предотвращает распознавание чужого файла (например, в ситуации, где 2 пользователя
        одновременно распознают разные файлы и их нужно распознать по отдельности) """
    abc = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([choice(abc) for _ in range(17)]) + '.mp3'


# Список стран и их кодов:
country_list = {
    'world': 'Мир',
    'AU': 'Австралия',
    'AT': 'Австрия',
    'BY': 'Беларусь',
    'UK': 'Великобритания',
    'DE': 'Германия',
    'DK': 'Дания',
    'ES': 'Испания',
    'IT': 'Италия',
    'CN': 'Китай',
    'PT': 'Португалия',
    'RU': 'Россия',
    'US': 'США',
    'RS': 'Сербия',
    'FI': 'Финляндия',
    'FR': 'Франция',
    'CH': 'Швейцария'
}


UNKNOWN_SONG = "https://i1.sndcdn.com/artworks-000417448131-gof0f8-t500x500.jpg"
