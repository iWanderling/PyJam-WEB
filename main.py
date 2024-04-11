from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request

from data.audio_handlers.recognize_handler import recognize_song, identifier
from data.audio_handlers.charts_handler import charts_handler, UNKNOWN_SONG

from data.forms.register_form import RegisterForm
from data.forms.login_form import LoginForm

from data.ORM import db_session
from data.ORM.recognized import Recognized, get_valid_date
from data.ORM.track import Track
from data.ORM.user import User

import os


# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'FFFFF0-JHKMQ1-KRMB89-KLLLVV-ZZHMN5'


# Инициализация объекта LoginManager, функции для загрузки пользователя:
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """ :Загрузка пользователя: """
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/', methods=["GET", "POST"])
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
        user = User()
        user.email = form.email.data
        user.surname = form.surname.data
        user.name = form.name.data

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


@app.route('/recognize', methods=["GET", "POST"])
def recognize():
    """ Данная функция предоставляет пользователю возможность распознать аудиофайл,
        который он отправляет на сервер с помощью специальной формы.

        После распознания трек записывается в специальную таблицу БД, чтобы в дальнейшем можно было
        поделиться треком и быстро отобразить его в библиотеке пользователя.

        Следующие параметры не являются обязательными и не передаются в функцию:

        message[str] - сообщение для пользователя
        waiting[bool] - ожидание ответа от распознающей функции; если False, то функция отобразит информацию о треке
        shazam_id[int] - ID трека в Shazam
        track[str] - название трека
        band[str] - название исполнителя
        background[str] - ссылка на обложку песни """

    # Если пользователь ничего не отправил - возвращаем обычную страницу
    if request.method == "GET":
        return render_template('recognize.html', waiting=True, background=UNKNOWN_SONG)

    # Если пользователь отправил файл на распознание, то возвращаем пользователю информацию о распознанном треке:
    elif request.method == "POST":

        # Загружаем отправленный пользователем файл:
        f = request.files['file']
        file_path = 'static/music/' + identifier()
        f.save(file_path)

        # Распознавание песни:
        track_data = recognize_song(file_path)
        os.remove(file_path)

        # Если программа не смогла определить трек, то уведомляем пользователя об этом:
        if track_data is None:
            return render_template('recognize.html', message='Not Found')

        # Если определение прошло успешно, то обрабатываем полученную информацию и формируем ответ:
        # Берём данные о треке:
        shazam_id, track_title, band, background = track_data

        # Проверяем, существует ли распознанный трек в БД:
        existing = db_sess.query(Track).filter(Track.shazam_id == shazam_id).first()

        # Если трека ещё нет в БД, то записываем информацию о нём,
        # а иначе - увеличиваем количество его распознаний:
        if not existing:
            track = Track()
            track.shazam_id = shazam_id
            track.track = track_title
            track.band = band
            track.background = background
            db_sess.add(track)
            db_sess.commit()
            track_id = track.id
        else:
            existing.popularity += 1
            track_id = existing.id
            db_sess.commit()

        # Если пользователь авторизован, то записываем информацию о
        # распознанном треке в его библиотеку:
        if current_user.is_authenticated:

            # Но если данный трек уже распознан, то просто обновляем время его распознания:
            already_recognized = db_sess.query(Recognized).filter(
                Recognized.track_id == track_id,
                Recognized.user_id == current_user.id
            ).first()

            if already_recognized:
                already_recognized.date = get_valid_date()
            else:
                recognized = Recognized()
                recognized.user_id = current_user.id
                recognized.track_id = track_id
                recognized.is_favourite = False

                db_sess.add(recognized)
            db_sess.commit()

        # Обновляем страницу:
        return redirect(f'/recognize/track/{track_id}')


@app.route('/recognize/track/<int:track_id>')
def track_info(track_id):
    """ Вернуть страницу с информацией о треке """
    track = db_sess.query(Track).filter(Track.id == track_id).first()
    return render_template('track.html', track=track)


@app.route('/library')
def user_library():
    """ Распознанные песни """
    if current_user.is_authenticated:
        library = list()
        recognized = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id).all()

        for i in recognized:
            track = db_sess.query(Track).filter(Track.id == i.id).first()
            library.append((track, i))

        return render_template('library.html', library=reversed(library))
    return render_template('library.html')


@app.route('/delete/track/<int:track_id>', methods=["GET"])
def delete_track(track_id):
    track_to_delete = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                       Recognized.track_id == track_id).first()
    db_sess.delete(track_to_delete)
    db_sess.commit()

    return redirect('/library')


@app.route('/charts', methods=["GET", "POST"])
def charts():
    """ Данная функция позволяет пользователю ознакомиться с мировым хит-парадом песен """
    world_top = charts_handler()
    return render_template('charts.html', world_top=world_top)


if __name__ == '__main__':
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()
    app.run(debug=True)
