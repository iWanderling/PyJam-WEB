from wtforms import PasswordField, StringField, IntegerField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Класс для регистрации пользователя
class RegisterForm(FlaskForm):
    email = EmailField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Регистрация')
