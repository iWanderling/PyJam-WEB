""" Пример: Распознать аудиофайл (необходимо использование ffmpeg.exe последней версии) """
from shazamio import Shazam
from random import choice
import asyncio
import string

def identifier():
    abc = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([choice(abc) for _ in range(9)]) + '.mp3'

def recognize_song(file='file.mp3'):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        rec = loop.run_until_complete(main(file))['track']
        title = rec['title']
        subtitle = rec['subtitle']
        background = rec['images']['background']
        return title, subtitle, background

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args[0])
        return message


async def main(file):
    return await Shazam().recognize(file)
