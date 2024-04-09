from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from datetime import datetime
from sqlalchemy import orm
import sqlalchemy


def get_valid_date():
    date = datetime.now()
    months = {
        '01': 'января',
        '02': 'февраля',
        '03': 'марта',
        '04': 'апреля',
        '05': 'мая',
        '06': 'июня',
        '07': 'июля',
        '08': 'августа',
        '09': 'сентября',
        '10': 'октября',
        '11': 'ноября',
        '12': 'декабря'
    }
    date = str(date).split()
    year, month, day = date[0].split('-')
    time = ':'.join(date[1].split(':')[:2])

    return f'{day} {months[month]}, {time}, {year}'


class Recognized(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'recognized'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    link = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Ссылка на изображение
    track = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Название песни
    band = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Название исполнителя

    # ID пользователя, который распознал музыку / песню:
    belonging = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))

    time = sqlalchemy.Column(sqlalchemy.String, default=get_valid_date)  # Время распознания
    is_favourite = sqlalchemy.Column(sqlalchemy.Boolean)  # Избранная ли песня

    # Связываемся с таблицей Users:
    user = orm.relationship('User')
