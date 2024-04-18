from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy


class Artist(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'artists'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    shazam_id = sqlalchemy.Column(sqlalchemy.Integer)  # ID исполнителя в Shazam
    artist = sqlalchemy.Column(sqlalchemy.String)  # Название исполнителя
    genre = sqlalchemy.Column(sqlalchemy.String)  # Жанр исполнителя
    background = sqlalchemy.Column(sqlalchemy.String)  # Ссылка на изображение
