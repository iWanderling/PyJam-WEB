from wtforms import PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# Форма для удаления аккаунта:
class DeleteProfileForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Пароль', validators=[DataRequired()])
    confirm = BooleanField('Я осознаю свои действия и понимаю, что не смогу восстановить свой аккаунт')
    submit = SubmitField('Удалить аккаунт')
