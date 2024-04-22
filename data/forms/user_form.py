from wtforms import EmailField, PasswordField, StringField, SubmitField, SelectField
from data.forms.gender_dropdown_field_form import Gender
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Форма для изменения личных данных:
class UserForm(FlaskForm):
    email = EmailField('Изменить E-Mail', validators=[DataRequired()])
    surname = StringField('Изменить фамилию', validators=[DataRequired()])
    name = StringField('Изменить имя', validators=[DataRequired()])
    gender = SelectField('Пол', choices=['Мужской', 'Женский'])
    submit = SubmitField('Подтвердить')
