from wtforms import StringField
from flask_wtf import FlaskForm


# Форма-выпадающий список с выбором пола. Применяется в формах регистрации и изменении личных данных в ЛК:
class Gender(FlaskForm):
    male = StringField('Мужской')
    female = StringField('Женский')
