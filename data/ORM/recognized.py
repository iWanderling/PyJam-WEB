from data.system_files.constants import get_valid_date

from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from datetime import datetime
from sqlalchemy import orm
import sqlalchemy


class Recognized(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'recognized'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    # ID пользователя, который распознал музыку / песню (связан с users.id):
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))

    # ID распознанного пользователем трека (связан с tracks.id):
    track_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tracks.id"))

    date = sqlalchemy.Column(sqlalchemy.String, default=get_valid_date)  # Время распознания
    is_favourite = sqlalchemy.Column(sqlalchemy.Boolean)  # Избранная ли песня

    # Связываемся с таблицей Users и Tracks:
    user = orm.relationship('User')
    track = orm.relationship('Track')
