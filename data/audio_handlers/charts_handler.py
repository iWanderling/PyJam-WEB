""" SHAZAM API -> Shazamio. Получение информации о хит-параде (по версии Shazam)

    ВАЖНОЕ ПРИМЕЧАНИЕ: В ПОСЛЕДНЕЕ ВРЕМЯ ЗАМЕЧЕН СБОЙ В РАБОТЕ ДАННОГО МОДУЛЯ. ОН СВЯЗАН С
    ТЕМ, ЧТО СЕРВЕР SHAZAM НЕ ПЕРЕДАЁТ ДАННЫЕ О ХИТ-ПАРАДАХ, СЛЕДОВАТЕЛЬНО, БИБЛИОТЕКА SHAZAMIO НЕ МОЖЕТ
    ПОЛУЧИТЬ НЕОБХОДИМУЮ ИНФОРМАЦИЮ. ЭТОТ СБОЙ НИКАК НЕ СВЯЗАН С РАБОТОЙ ПРОЕКТА PYJAM. ЕСЛИ ДО ЗАЩИТЫ СБОЙ
    БУДЕТ ПРОДОЛЖАТЬСЯ, ТО МЫ БУДЕМ ВЫНУЖДЕНЫ ДОБАВИТЬ ЕЩЁ ОДНУ СТРАНИЦУ, ЗА СЧЁТ КОТОРОЙ ОБЪЁМ ПРОДЕЛАННОЙ
    РАБОТЫ НЕ СНИЗИТСЯ. БУДЕМ НАДЕЯТЬСЯ НА ТО, ЧТО КОМАНДА РАЗРАБОТЧИКОВ SHAZAM СМОЖЕТ ИСПРАВИТЬ ДАННУЮ ПРОБЛЕМУ.

"""
from shazamio import Shazam, GenreMusic
from data.system_files.constants import UNKNOWN_SONG, LIMIT_CONSTANT
import asyncio


# Специальное условие асинхронной функции для ОС Windows:
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Словарь с жанрами. Значения словаря должны подаваться на вход функции для получения информации:
genres_library = {
    'alternative': GenreMusic.ALTERNATIVE,
    'pop': GenreMusic.POP,
    'rock': GenreMusic.ROCK,
    'dance': GenreMusic.DANCE,
    'electronic': GenreMusic.ELECTRONIC,
    'country': GenreMusic.COUNTRY,
    'afro': GenreMusic.AFRO_BEATS,
    'rap-hip-hop': GenreMusic.HIP_HOP_RAP
}


async def world_top():
    """ Функция возвращает информацию о самых популярных треках в мире.
        LIMIT_CONSTANT - количество позиций в топе. """
    return await Shazam().top_world_tracks(limit=LIMIT_CONSTANT)


async def world_top_by_genre(genre):
    """ Функция возвращает информацию о самых популярных треках в мире в определённом жанре.
        Genre[str] - жанр, по которому нужно произвести запрос;
        LIMIT_CONSTANT - количество позиций в топе. """
    get_g = genres_library[genre]
    return await Shazam().top_world_genre_tracks(genre=get_g, limit=LIMIT_CONSTANT)


async def country_top(country):
    """ Функция возвращает информацию о самых популярных треках в определённой стране.
        Country[str] - страна, по которой нужно произвести запрос;
        LIMIT_CONSTANT - количество позиций в топе."""
    return await Shazam().top_country_tracks(country, LIMIT_CONSTANT)


async def country_top_by_genre(country, genre):
    """ Функция возвращает информацию о самых популярных треках в определённой стране и в определённом жанре.
        Country[str] - страна, по которой нужно произвести запрос.
        Genre[str] - жанр, по которому нужно произвести запрос. В данном случае выступает в роли фильтра;
        LIMIT_CONSTANT - количество позиций в топе. """
    get_g = genres_library[genre]
    return await Shazam().top_country_genre_tracks(country_code=country, genre=get_g,
                                                   limit=LIMIT_CONSTANT)


def charts_handler(country, genre=None):
    """ Данная функция обрабатывает полученные от пользователя данные, а затем возвращает информацию о
        хит-парадах*, исходя из избранных фильтров.

        Country[str] - страна, по которой нужно произвести запрос.
        Genre[str] - жанр, по которому нужно произвести запрос. В данном случае выступает в роли фильтра.

        *По версии Shazam """

    # Создаём список, который будем отправлять на сервер сайта. В нём будет храниться данные со всеми треками,
    # включенными в хит-парад:
    rating = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Фильтрация запроса:
    if genre is None:
        if country == 'world':
            data = loop.run_until_complete(world_top())['tracks']
        else:
            data = loop.run_until_complete(country_top(country))['tracks']
    else:
        if country == 'world':
            data = loop.run_until_complete(world_top_by_genre(genre))['tracks']
        else:
            data = loop.run_until_complete(country_top_by_genre(country, genre))['tracks']

    # Создание списка списков с информацией о топе:
    for i in data:
        dataset = dict()

        # Добавляем artist_id (на сайте Shazam - это shazam_id исполнителя):
        dataset['artist_id'] = 0
        if 'artists' in i:
            dataset['artist_id'] = i['artists'][0]['adamid']

        # Добавляем ссылку на изображение:
        dataset['background'] = UNKNOWN_SONG
        if 'image' in i['share']:
            dataset['background'] = i['share']['image']

        # Shazam_id песни:
        if 'actions' in i['hub']:
            dataset['shazam_id'] = i['hub']['actions'][0]['id']

        # Название трека, название исполнителя, специальный ключ для работы с треком:
        dataset['track'] = i['title']
        dataset['band'] = i['subtitle']
        dataset['track_key'] = i['key']

        # Добавляем информацию:
        rating.append(dataset)
    return rating


# Архивная функция: найти доступные фильтры по жанрам для отдельной страны (не учитывается в общей сумме строк кода)
# def find_available_genres(country):
#     available = list()
#
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#
#     for g in genres_library.keys():
#         try:
#             data = loop.run_until_complete(country_top_by_genre(country, g))['tracks']
#             available.append(g)
#         except FailedDecodeJson:
#             pass
#     return available
