""" Модуль позволяет получить самую популярную во всём мире музыку / песню """
from shazamio import Shazam
import asyncio


UNKNOWN_SONG = "https://i1.sndcdn.com/artworks-000417448131-gof0f8-t500x500.jpg"


async def main(limit_constant):
    """ Получить информацию о самых популярных треках в мире """
    return await Shazam().top_world_tracks(limit=limit_constant)


def charts_handler(limit_constant=25):
    """ Получить информацию о самых популярных треках в мире
            limit_constant[int] -> необязательный параметр; получить первые N позиций в топе """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    data = loop.run_until_complete(main(limit_constant))['tracks']
    world_top = []

    # Создание списка списков с информацией о топе:
    for i in data:
        dataset = [i['title'], i['subtitle']]
        if 'image' in i['share']:
            dataset.append(i['share']['image'])
        else:
            dataset.append(UNKNOWN_SONG)
        world_top.append(dataset)
    return world_top
