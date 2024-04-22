""" REST-API для сбора JSON-файла с данными об исполнителях на платформе """
from flask_restful import Resource, Api, abort
from data.ORM.artist import Artist
from data.ORM.track import Track
from data.ORM import db_session
from flask import jsonify
import requests


# Возврат сообщения о работе сервера:
def abort_404(artist_id):
    session = db_session.create_session()
    artist = session.query(Artist).get(artist_id)
    if not artist:
        abort(404)


# Класс REST-API для сбора данных об одном исполнителе с ID в БД: [artist_id]:
class ArtistJsonAPI(Resource):
    def get(self, artist_id):

        # Проверяем существование исполнителя с ID [artist_id]:
        abort_404(artist_id)

        # Создаём сессию, загружаем информацию и отправляем её:
        session = db_session.create_session()
        artist = session.query(Artist).get(artist_id)

        get_data = dict()

        if artist.id:
            get_data['platform_id'] = artist.id
        get_data['shazam_id'] = artist.shazam_id
        get_data['name'] = artist.artist
        get_data['genre'] = artist.genre
        get_data['recognized'] = sum([t.popularity for t in
                                      session.query(Track).filter(Track.artist_id == artist.shazam_id).all()])
        get_data['track_on_platform'] = len(session.query(Track).filter(Track.artist_id == artist.shazam_id).all())
        return jsonify({'artist': get_data})


# Класс REST-API для сбора данных о всех исполнителях на платформе:
class ArtistAllJsonAPI(Resource):
    def get(self):

        # Создаём сессию, загружаем информацию и отправляем её:
        session = db_session.create_session()
        artists = session.query(Artist).all()

        get_data = dict()
        get_data['artist'] = []

        for artist in artists:
            artist_data = dict()
            if artist.id:
                artist_data['platform_id'] = artist.id
            artist_data['shazam_id'] = artist.shazam_id
            artist_data['name'] = artist.artist
            artist_data['genre'] = artist.genre
            artist_data['recognized'] = sum([t.popularity for t in
                                          session.query(Track).filter(Track.artist_id == artist.shazam_id).all()])
            artist_data['track_on_platform'] = len(session.query(Track).filter(Track.artist_id == artist.shazam_id).all())

            get_data['artist'].append(artist_data)

        return jsonify({'artists': get_data})
