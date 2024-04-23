""" SHAZAM API -> Shazamio. Распознавание трека по аудиофайлу.

    ВНИМАНИЕ: ДЛЯ РАБОТЫ ФУНКЦИИ НЕОБХОДИМО ИСПОЛЬЗОВАНИЕ FFMPEG.EXE ПОСЛЕДНЕЙ ВЕРСИИ.
    ДАННЫЙ ФАЙЛ ДОЛЖЕН ХРАНИТЬСЯ В РАБОЧЕЙ ДИРЕКТОРИИ ПРОЕКТА ИЛИ ИМЕТЬ ДОСТУП В PATH.
"""
from shazamio import Shazam
from data.system_files.constants import *
import asyncio


# Специальное условие асинхронной функции для ОС Windows:
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def recognize_song(file: str):
    """ Данная функция распознает аудиофайл, а затем возвращает данные о распознанном треке. """
    return await Shazam().recognize(file)


def recognize_song_handler(file, all_info=None):
    """ Данная функция-обработчик получает информацию о распознанном треке, а затем заворачивает данные
        в удобный и понятный массив и возвращает его.

        File - имя файла;
        all_info[bool] - необходимо ли вернуть полную информацию о треке. """

    # Получаем данные:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        data = loop.run_until_complete(recognize_song(file))  # Получение информации о распознанном файле

        # Если полная информация не нужна,
        # то функция вернёт название трека и исполнителя, а также ссылку альбома трека:
        if all_info is None:
            track_key = data['track']['key']  # Ключ трека
            artist_id = data['track']['artists'][0]['adamid']  # Shazam_id исполнителя трека:
            title = data['track']['title']  # Название песни
            band = data['track']['subtitle']  # Название исполнителя
            shazam_id = data['matches'][0]['id']  # ID песни в Shazam (Track_Shazam_ID)

            # Ссылка на изображение обложки песни
            if 'images' in data['track']:
                background = data['track']['images']['background']
            else:
                background = UNKNOWN_SONG

            # Возвращаем указанную информацию:
            return track_key, shazam_id, artist_id, title, band, background

        # Возвращаем полную информацию:
        return data

    # Если распознать трек не удалось, то возвращаем None:
    except KeyError:
        return None
