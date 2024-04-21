""" Модуль позволяет распознать практически любой аудиофайл, отправленный пользователем сайта
   (примечание: необходимо использование ffmpeg.exe последней версии) """
from shazamio import Shazam
from data.system_files.constants import *
import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main(file: str):
    """ Распознать аудиофайл [file] """
    return await Shazam().recognize(file)


def recognize_song(file='file.mp3', all_info=None):
    """ Распознать аудиофайл, название которого передано в функцию.
        Для распознавания используется функция main().

        ::Параметры::
        file[str] -> путь к аудиофайлу
        all_info[bool] -> необязательный аргумент; указывает,
                          нужно ли возвращать полную информацию о треке """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        data = loop.run_until_complete(main(file))  # получение информации о распознанном файле

        # Если полная информация не нужна,
        # то функция вернёт название трека и исполнителя, а также ссылку альбома трека:
        if all_info is None:
            track_key = data['track']['key']
            artist_id = data['track']['artists'][0]['adamid']
            title = data['track']['title']  # название песни
            band = data['track']['subtitle']  # название исполнителя
            shazam_id = data['matches'][0]['id']  # ID песни в Shazam
            if 'images' in data['track']:
                background = data['track']['images']['background']  # ссылка на изображение альбома песни
            else:
                background = UNKNOWN_SONG

            # Возвращаем указанную информацию:
            return track_key, shazam_id, artist_id, title, band, background

        # Возвращаем полную информацию:
        return data

    # Если распознать трек не удалось, то возвращаем None:
    except KeyError:
        return None
