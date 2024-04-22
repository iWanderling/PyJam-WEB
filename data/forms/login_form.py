from wtforms import PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Форма для авторизации:
class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
