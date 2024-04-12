""" Модуль позволяет получить самую популярную во всём мире музыку / песню """
from shazamio import Shazam
from pprint import pprint
import asyncio


UNKNOWN_SONG = "https://i1.sndcdn.com/artworks-000417448131-gof0f8-t500x500.jpg"
LIMIT_CONSTANT = 100


async def world_top():
    """ Вернуть информацию о самых популярных треках в мире """
    return await Shazam().top_world_tracks(limit=LIMIT_CONSTANT)


async def country_top(country):
    """ Вернуть информацию о самых популярных треках в стране <country> """
    return await Shazam().top_country_tracks(country, LIMIT_CONSTANT)


def charts_handler(country):
    """ Получить информацию о самых популярных треках """

    rating = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if country == 'world':
        data = loop.run_until_complete(world_top())['tracks']
    else:
        data = loop.run_until_complete(country_top(country))['tracks']

    # Создание списка списков с информацией о топе:
    for i in data:
        dataset = dict()
        if 'actions' in i['hub']:
            dataset['shazam_id'] = i['hub']['actions'][0]['id']
        dataset['track'] = i['title']
        dataset['band'] = i['subtitle']

        if 'image' in i['share']:
            dataset['background'] = i['share']['image']
        else:
            dataset['background'] = UNKNOWN_SONG

        rating.append(dataset)
    return rating

