import asyncio
from shazamio import Shazam
from pprint import pprint
from data.constants import *


async def similiar_songs(track_key):
    shazam = Shazam()

    data = await shazam.related_tracks(track_id=track_key)

    related = list()
    for i in data['tracks']:
        track_key = i['key']

        artist_id = 0
        if 'artists' in i:
            artist_id = i['artists'][0]['adamid']

        shazam_id = 0
        if 'actions' in i['hub']:
            shazam_id = i['hub']['actions'][0]['id']

        background = UNKNOWN_SONG
        if 'image' in i['share']:
            background = i['share']['image']

        track = i['title']
        band = i['subtitle']

        related.append([track_key, shazam_id, artist_id, track, band, background])
    return related

def get_similiar_songs(track_key):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(similiar_songs(track_key))

