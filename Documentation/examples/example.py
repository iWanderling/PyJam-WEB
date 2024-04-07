""" Пример: Распознать аудиофайл (необходимо использование ffmpeg.exe последней версии) """
import asyncio
from shazamio import Shazam


async def main():
    shazam = Shazam()
    out = await shazam.recognize('file.mp3')  # rust version, use this
    print(out)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
