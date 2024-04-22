from werkzeug.security import generate_password_hash, check_password_hash
from data.system_files.constants import get_valid_date
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
import sqlalchemy


# Класс для создания таблицы с пользователями:
class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)  # E-MAIL пользователя
    surname = sqlalchemy.Column(sqlalchemy.String)  # Фамилия пользователя
    name = sqlalchemy.Column(sqlalchemy.String)  # Имя пользователя
    gender = sqlalchemy.Column(sqlalchemy.String)  # Пол (Мужской / Женский) пользователя
    hashed_password = sqlalchemy.Column(sqlalchemy.String)  # Пароль пользователя

    # ID уникальных треков, которые распознал пользователь (разделитель - &):
    unique = sqlalchemy.Column(sqlalchemy.String, default='')

    # Всего распознано уникальных треков:
    unique_total = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    background = sqlalchemy.Column(sqlalchemy.String)  # Изображение профиля
    date = sqlalchemy.Column(sqlalchemy.String, default=get_valid_date)  # Дата регистрации
    warns = sqlalchemy.Column(sqlalchemy.Integer, default=0)  # Количество предупреждений

    # Кэшировать пароль:
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    # Расшифровать пароль (необходимо указать текущий пароль):
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
