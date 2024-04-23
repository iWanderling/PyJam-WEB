""" SHAZAM API -> Shazamio. Получение информации о похожих на определённый трек песнях. """
from data.system_files.constants import *
from shazamio import Shazam
import asyncio


async def similiar_songs(track_key):
    """ Данная функция обрабатывает и возвращает информацию о похожих на определённый трек песнях.

        Track_key - специальный ключ трека, по которому можно получить данную информацию. """

    # Получение информации:
    data = await Shazam().related_tracks(track_id=track_key)

    # Создаём список, в который будем записывать данные о треках, а затем отправим его на сервер:
    related = list()
    for i in data['tracks']:
        track_key = i['key']  # Ключ трека

        # ShazamID исполнителя трека:
        artist_id = 0
        if 'artists' in i:
            artist_id = i['artists'][0]['adamid']

        # ShazamID трека:
        shazam_id = 0
        if 'actions' in i['hub']:
            shazam_id = i['hub']['actions'][0]['id']

        # Обложка трека:
        background = UNKNOWN_SONG
        if 'image' in i['share']:
            background = i['share']['image']

        # Название трека, название исполнителя:
        track = i['title']
        band = i['subtitle']

        # Добавление информации:
        related.append([track_key, shazam_id, artist_id, track, band, background])
    return related


# Обработчик функции:
def get_similiar_songs(track_key):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(similiar_songs(track_key))
