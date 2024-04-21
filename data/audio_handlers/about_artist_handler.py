from shazamio.schemas.artists import ArtistQuery
from shazamio.schemas.enums import ArtistView
from shazamio import Shazam
from pprint import pprint
import asyncio


def artwork_handler(artwork):
    """ Функция возвращает аватарку исходя из переданного параметра artwork;
        artwork[dict] -> словарь со ссылкой на изображение, а также шириной и высотой изображения """
    width = artwork['width']
    height = artwork['height']
    url = artwork['url']

    valid_url = url.replace('{w}', str(width)).replace('{h}', str(height))
    return valid_url


async def best_artist_tracks(artist_id):
    """ Функция возвращает самые популярные треки определённого исполнителя
        Примечание: на странице отображается ТОП-3 трека, и вместе с остальными треками они загружаются в БД """
    shazam = Shazam()
    about_artist = await shazam.artist_about(artist_id,
                                             query=ArtistQuery(views=[ArtistView.TOP_SONGS]))
    return about_artist


async def artist_info(artist_id):
    """ Функция возвращает краткую информацию об исполнителе
        artist_id[int] -> ID исполнителя, по которому будем искать его с помощью Shazamio """

    shazam = Shazam()
    about_artist = await shazam.artist_about(artist_id)

    if about_artist:
        about_artist = about_artist['data'][0]['attributes']
        artist_name = about_artist['name']  # Название исполнителя

        try:
            artist_genre = about_artist['genreNames'][0]  # Жанр исполнителя
        except IndexError:
            artist_genre = 'Неизвестен'

        artist_artwork = about_artist['artwork']  # [Артворк] с данными об изображении исполнителя
        artist_background = artwork_handler(artist_artwork)  # Ссылка на изображение

        artist_best = await best_artist_tracks(artist_id)  # Возвращаем информацию с лучшими треками исполнителя
        artist_best = artist_best['data'][0]['views']['top-songs']['data']

        artist_best_tracks = list()

        for i in artist_best:
            # Получаем ID трека, а если его нет, то устанавливаем значение 0 (трек не найден)
            try:
                track_id = i['id']
            except KeyError:
                track_id = 0

            track = i['attributes']  # информация о треке
            title = track['name']  # название трека
            band = artist_name  # название исполнителя
            track_artwork = track['artwork']  # [Артворк] с данными об изображении
            track_background = artwork_handler(track_artwork)

            artist_best_tracks.append([track_id, title, band, track_background])

        return ([artist_id, artist_name, artist_genre, artist_background],
                artist_best_tracks)
    return None

def get_artist_info(artist_id):
    """ Обработчик функции get_artist """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    return loop.run_until_complete(artist_info(artist_id))
