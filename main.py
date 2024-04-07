from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request, abort, make_response, jsonify

from data.forms.register_form import RegisterForm
from data.forms.login_form import LoginForm

from data.ORM import db_session
from data.ORM.user import *


# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'FFFFF0-JHKMQ1-KRMB89-KLLLVV-ZZHMN5'


# Инициализация объекта LoginManager, функции для загрузки пользователя:
login_manager = LoginManager()
login_manager.init_app(app)


# Загрузка пользователя:
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def main():
    """ Главная страница """
    return render_template('main.html')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    """ Страница для регистрации пользователя """

    # Создание объекта регистрационной формы (RegisterForm)
    # Форма обрабатывает введённые пользователем данные,
    # и если все данные введены верно, то регистрирует пользователя в системе:
    form = RegisterForm()

    # Обработка нажатия на кнопку (Зарегистрироваться)
    if form.validate_on_submit():
        # Проверка пароля на надёжность (слабая, доработать)
        if any([len(form.password.data) <= 9, form.password.data.isdigit()]):
            return render_template('register.html', title='Регистрация',
                                   message="Пароль содержит менее 9 символов или содержит только цифры",
                                   form=form)

        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")

        # Создаём сессию, проверяем, существуют ли введённые пользователем данные в БД;
        # Если данные уже есть в базе, то отправляем соответствующее сообщение,
        # иначе - продолжаем процесс регистрации:
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        # Создание объекта класса пользователя (User):
        user = User(
            email=form.email.data,
            surname=form.surname.data,
            name=form.name.data)

        # Шифруем пароль пользователя и регистрируем его:
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        # Отправляем пользователя на страницу для авторизации:
        return redirect('/login')

    # Отображение страницы регистрации:
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Страница для авторизации пользователя """

    # Создание объекта формы для входа в аккаунт (LoginForm)
    # Форма обрабатывает введённые пользователем данные,
    # и если все данные введены верно, то авторизует пользователя в системе:
    form = LoginForm()

    # Обработка нажатия на кнопку (Войти)
    if form.validate_on_submit():

        # Создание сессии, обработка введённых пользователем данных
        # Незамедлительно авторизуем пользователя при успешном прохождении авторизации:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        # Авторизация:
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")

        # Если пользователь ввёл некорректные данные, то выводим соответствующее сообщение:
        return render_template('login.html', message="Неправильный логин или пароль", form=form)

    # Отображение страницы авторизации:
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    """ Функция обрабатывает выход пользователя из аккаунта """
    logout_user()
    return redirect("/")

@app.route('/recognize')
def recognize():
    return render_template('recognize.html')


@app.route('/charts')
def charts():
    return render_template('charts.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()
    app.run(debug=True)
