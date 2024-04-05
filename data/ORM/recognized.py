from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy
import datetime


class Recognized(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'recognized'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    link = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Ссылка на изображение
    track = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Название песни
    band = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Название исполнителя

    # ID пользователя, который распознал музыку / песню:
    belonging = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))

    time = sqlalchemy.Column(sqlalchemy.String, default=datetime.datetime.now)  # Время распознания
    is_favourite = sqlalchemy.Column(sqlalchemy.Boolean)  # Избранная ли песня

    # Связываемся с таблицей Users:
    user = orm.relationship('User')
