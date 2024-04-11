""" Модуль позволяет распознать практически любой аудиофайл, отправленный пользователем сайта
   (примечание: необходимо использование ffmpeg.exe последней версии) """
from shazamio import Shazam
from random import choice
import asyncio
import string


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
UNKNOWN_SONG = "https://i1.sndcdn.com/artworks-000417448131-gof0f8-t500x500.jpg"


def identifier():
    """ Создаёт уникальное имя для файла, который нужно распознать.
        Предотвращает распознавание чужого файла (например, в ситуации, где 2 пользователя
        одновременно распознают разные файлы и их нужно распознать по отдельности) """
    abc = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([choice(abc) for _ in range(17)]) + '.mp3'


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
            title = data['track']['title']  # название песни
            band = data['track']['subtitle']  # название исполнителя
            shazam_id = data['matches'][0]['id']  # ID песни в Shazam
            if 'images' in data['track']:
                background = data['track']['images']['background']  # ссылка на изображение альбома песни
            else:
                background = UNKNOWN_SONG

            # Возвращаем указанную информацию:
            return shazam_id, title, band, background

        # Возвращаем полную информацию:
        return data

    # Если распознать трек не удалось, то возвращаем None:
    except KeyError:
        return None
