from recognize_handler import recognize_song
from shazamio import Shazam
import asyncio
from pprint import pprint

async def similiar(track_id, limit_constant=3, offset_constant=3):
    """ Получить треки, схожие по жанру и звучанию с определённой песней

        ::Параметры::
        track_id[int] -> ID песни в Shazam
        limit_constant[int] -> необязательный параметр; сколько похожих песен нужно получить (по умолчанию - 3)
        offset_constant[int] -> необязательный параметр; """

    return await Shazam().related_tracks(track_id=track_id, limit=limit_constant,
                                         offset=offset_constant)


# Пример работы программы:
track_id = recognize_song(all_info=True)['matches'][0]["id"]
loop = asyncio.get_event_loop()
a = loop.run_until_complete(similiar(track_id))
pprint(a['tracks'])

