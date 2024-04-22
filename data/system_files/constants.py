from datetime import datetime
from random import choice
import string


# Количество треков, которые нужно отобразить в топе:
LIMIT_CONSTANT = 100


def identifier(format_):
    """ Создаёт уникальное имя для файла, который нужно распознать.
        Предотвращает распознавание чужого файла (например, в ситуации, где 2 пользователя
        одновременно распознают разные файлы и их нужно распознать по отдельности) """
    abc = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([choice(abc) for _ in range(17)]) + format_


# Получение текущей даты формата: [день] [месяц], [время], [год].
# Применяется, в основном, в ORM-классах для получения текущей даты с целью её записи в БД:
def get_valid_date():
    date = datetime.now()
    months = {
        '01': 'января',
        '02': 'февраля',
        '03': 'марта',
        '04': 'апреля',
        '05': 'мая',
        '06': 'июня',
        '07': 'июля',
        '08': 'августа',
        '09': 'сентября',
        '10': 'октября',
        '11': 'ноября',
        '12': 'декабря'
    }
    date = str(date).split()
    year, month, day = date[0].split('-')
    time = ':'.join(date[1].split(':')[:2])

    return f'{day} {months[month]}, {time}, {year}'


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

# Жанры:
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

# Доступные жанры для каждой страны (применяется на странице хит-парадов)
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

# Изображения
UNKNOWN_SONG = 'unknown_song.png'
MAN_PROFILE_PICTURE = 'img/user_profile/man.png'
WOMAN_PROFILE_PICTURE = 'img/user_profile/woman.png'
