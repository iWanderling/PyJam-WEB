from wtforms import PasswordField, StringField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Класс для регистрации пользователя
class UserForm(FlaskForm):
    email = EmailField('Изменить E-Mail', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    new_password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Изменить фамилию', validators=[DataRequired()])
    name = StringField('Изменить имя', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
