from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy


class Track(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tracks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    shazam_id = sqlalchemy.Column(sqlalchemy.Integer)  # ID песни в Shazam
    track = sqlalchemy.Column(sqlalchemy.String)  # Название песни
    band = sqlalchemy.Column(sqlalchemy.String)  # Название исполнителя
    background = sqlalchemy.Column(sqlalchemy.String)  # Ссылка на изображение
    popularity = sqlalchemy.Column(sqlalchemy.Integer, default=1)  # Сколько раз трек был распознан
