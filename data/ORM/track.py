from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy


class Track(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tracks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    shazam_id = sqlalchemy.Column(sqlalchemy.Integer)  # ID песни в Shazam
    track_key = sqlalchemy.Column(sqlalchemy.Integer)  # KEY (ключ) для особой работы с ShazamAPI (поиск похожих треков)
    # ID исполнителя данной песни
    artist_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("artists.shazam_id"))
    track = sqlalchemy.Column(sqlalchemy.String)  # Название песни
    band = sqlalchemy.Column(sqlalchemy.String)  # Название исполнителя
    background = sqlalchemy.Column(sqlalchemy.String)  # Ссылка на изображение
    popularity = sqlalchemy.Column(sqlalchemy.Integer, default=1)  # Сколько раз трек был распознан

    # Связываемся с таблицей Artists:
    user = orm.relationship('Artist')
