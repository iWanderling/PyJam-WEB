""" Модуль позволяет распознать практически любой аудиофайл, отправленный пользователем сайта
   (примечание: необходимо использование ffmpeg.exe последней версии) """
from shazamio import Shazam
from random import choice
import asyncio
import string


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
            subtitle = data['track']['subtitle']  # название исполнителя
            background = data['track']['images']['background']  # ссылка на изображение альбома песни
            return title, subtitle, background
        return data  # возврат полной информация

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args[0])
        return message
