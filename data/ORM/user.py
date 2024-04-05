from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
import sqlalchemy
import datetime

from .db_session import SqlAlchemyBase

class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    # Кэшировать пароль
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    # Расшифровать пароль
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
