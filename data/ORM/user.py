from data.system_files.constants import get_valid_date
from .db_session import SqlAlchemyBase

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
import sqlalchemy
import datetime


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    gender = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    unique = sqlalchemy.Column(sqlalchemy.String, default='')
    unique_total = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    background = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(sqlalchemy.String, default=get_valid_date)
    warns = sqlalchemy.Column(sqlalchemy.Integer, default=0)  # количество предупреждений

    # Кэшировать пароль
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    # Расшифровать пароль
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
