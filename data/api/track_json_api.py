from flask_restful import Resource, Api, abort
from flask_login import current_user
from data.ORM.track import Track
from data.ORM import db_session
from flask import jsonify
import requests


# Возврат сообщения о работе сервера
def abort_404(track_id):
    session = db_session.create_session()
    track = session.query(Track).get(track_id)
    if not track:
        abort(404)


class TrackJsonAPI(Resource):
    def get(self, track_id):
        abort_404(track_id)
        session = db_session.create_session()
        track = session.query(Track).get(track_id)

        get_data = dict()
        if track.id:
            get_data['platform_id'] = track.id
        get_data['shazam_id'] = track.shazam_id
        get_data['title'] = track.track
        get_data['band'] = track.band
        get_data['popularity'] = track.popularity

        return jsonify({'track': get_data})

class TrackAllJsonAPI(Resource):
    def get(self):
        session = db_session.create_session()
        tracks = session.query(Track).all()

        get_data = dict()
        get_data['track'] = []

        for track in tracks:
            track_data = dict()
            if track.id:
                track_data['platform_id'] = track.id
            track_data['shazam_id'] = track.shazam_id
            track_data['title'] = track.track
            track_data['band'] = track.band
            track_data['popularity'] = track.popularity

            get_data['track'].append(track_data)

        return jsonify({'tracks': get_data})
