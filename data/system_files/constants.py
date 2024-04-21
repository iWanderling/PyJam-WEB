from random import choice
import string


LIMIT_CONSTANT = 100


def identifier(format_):
    """ Создаёт уникальное имя для файла, который нужно распознать.
        Предотвращает распознавание чужого файла (например, в ситуации, где 2 пользователя
        одновременно распознают разные файлы и их нужно распознать по отдельности) """
    abc = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([choice(abc) for _ in range(17)]) + format_


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

genres_list = {
    'Все жанры': 'Все жанры',
    'pop': 'Поп',
    'country': 'Кантри',
    'rock': 'Рок',
    'afro': "Афро",
    'alternative': "Альтернатива",
    'dance': "Танцевальная",
    'electronic': "Электронная",
    'rap-hip-hop': "Хип-хоп / Рэп"
}

AVAILABLE_GENRES = {
    'world': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'AU': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'AT': [],
    'BY': [],
    'UK': [],
    'DE': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'DK': [],
    'ES': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'IT': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'CN': [],
    'PT': [],
    'RU': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'US': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'RS': [],
    'FI': [],
    'FR': ['alternative', 'pop', 'rock', 'dance', 'electronic', 'country', 'afro', 'rap-hip-hop'],
    'CH': []
}

UNKNOWN_SONG = 'unknown_song.png'
