""" Модуль позволяет получить самую популярную во всём мире музыку / песню """
from shazamio import Shazam, GenreMusic
from data.system_files.constants import UNKNOWN_SONG, LIMIT_CONSTANT
import asyncio


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
    """ Вернуть информацию о самых популярных треках в мире """
    return await Shazam().top_world_tracks(limit=LIMIT_CONSTANT)

async def world_top_by_genre(genre):
    """ Вернуть информацию о самых популярных треках в мире в определённом жанре """
    get_g = genres_library[genre]
    return await Shazam().top_world_genre_tracks(genre=get_g, limit=LIMIT_CONSTANT)

async def country_top(country):
    """ Вернуть информацию о самых популярных треках в стране <country> """
    return await Shazam().top_country_tracks(country, LIMIT_CONSTANT)

async def country_top_by_genre(country, genre):
    """ Вернуть информацию о самых популярных треках в стране и в определённом жанре """
    get_g = genres_library[genre]
    return await Shazam().top_country_genre_tracks(country_code=country, genre=get_g,
                                                   limit=LIMIT_CONSTANT)


def charts_handler(country, genre=None):
    """ Получить информацию о самых популярных треках """

    rating = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

        dataset['artist_id'] = 0
        if 'artists' in i:
            dataset['artist_id'] = i['artists'][0]['adamid']

        dataset['background'] = UNKNOWN_SONG
        if 'image' in i['share']:
            dataset['background'] = i['share']['image']

        if 'actions' in i['hub']:
            dataset['shazam_id'] = i['hub']['actions'][0]['id']

        dataset['track'] = i['title']
        dataset['band'] = i['subtitle']
        dataset['track_key'] = i['key']

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
