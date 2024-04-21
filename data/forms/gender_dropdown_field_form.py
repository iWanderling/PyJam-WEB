from wtforms import StringField
from flask_wtf import FlaskForm


class Gender(FlaskForm):
    male = StringField('Мужской')
    female = StringField('Женский')
