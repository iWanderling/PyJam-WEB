from wtforms import PasswordField, StringField, IntegerField, SubmitField, EmailField, SelectField
from data.forms.gender_dropdown_field_form import Gender
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Форма для регистрации:
class RegisterForm(FlaskForm):
    email = EmailField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    gender = SelectField('Пол', choices=['Мужской', 'Женский'])
    submit = SubmitField('Регистрация')
