# Модули для работы с Flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request, jsonify

# Обработчики ShazamAPI
from data.audio_handlers.recognize_handler import recognize_song, identifier
from data.audio_handlers.charts_handler import charts_handler, UNKNOWN_SONG
from data.audio_handlers.similiar_songs_handler import *
from data.audio_handlers.about_artist_handler import *

# Форма регистрации и авторизации
from data.forms.register_form import RegisterForm
from data.forms.login_form import LoginForm

# ORM-модели
from data.ORM import db_session
from data.ORM.recognized import Recognized, get_valid_date
from data.ORM.artist import Artist
from data.ORM.track import Track
from data.ORM.user import User

# Константы
from data.constants import *

# Для удаления загруженных на сервер файлов
import os


# Инициализация приложения:
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
        shazam_id[int] - ID трека в Shazam
        track[str] - название трека
        band[str] - название исполнителя
        background[str] - ссылка на обложку песни """

    # Если пользователь ничего не отправил - возвращаем обычную страницу
    if request.method == "GET":
        return render_template('recognize.html', background=UNKNOWN_SONG)

    # Если пользователь отправил файл на распознание, то возвращаем пользователю информацию о распознанном треке:
    elif request.method == "POST":

        # Загружаем отправленный пользователем файл, если пользователь ничего не отправил - перезагружаем страницу:
        f = request.files['file']
        if not f.filename:
            return render_template('recognize.html', message='Вы не отправили файл', background=UNKNOWN_SONG)
        file_path = 'static/music/' + identifier()
        f.save(file_path)

        # Распознавание песни:
        track_data = recognize_song(file_path)
        os.remove(file_path)
        # Если программа не смогла определить трек, то уведомляем пользователя об этом:
        if track_data is None:
            return redirect('/recognize/track/0')

        # Если определение прошло успешно, то обрабатываем полученную информацию и формируем ответ:
        # Берём данные о треке:
        shazam_id, artist_id, track_title, band, background = track_data

        # Проверяем, существует ли распознанный трек в БД:
        existing = db_sess.query(Track).filter(Track.shazam_id == shazam_id).first()

        # Если трека ещё нет в БД, то записываем информацию о нём,
        # а иначе - увеличиваем количество его распознаний:
        if not existing:
            track = Track()
            track.shazam_id = shazam_id
            track.artist_id = artist_id
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


@app.route('/Charts/<country>/<genre>', methods=["GET", "POST"])
@app.route('/charts/<country>', methods=["GET", "POST"])
@app.route('/charts', methods=["GET", "POST"])
def charts(country=None, genre=None):
    """ Данная функция позволяет пользователю ознакомиться с мировым хит-парадом песен """

    # Возвращаем мировой топ, если не введены параметры в адрес:
    if country is None and genre is None:
        return redirect('/charts/world')

    top = charts_handler(country=country)

    for i in top:
        if 'shazam_id' in i:
            existing = db_sess.query(Track).filter(Track.shazam_id == i['shazam_id']).first()

            if not existing:
                track = Track()
                track.shazam_id = i['shazam_id']
                track.artist_id = i['artist_id']
                track.track = i['track']
                track.band = i['band']
                track.background = i['background']
                track.popularity = 0
                db_sess.add(track)
                db_sess.commit()

                i['db_id'] = track.id
            else:
                i['db_id'] = db_sess.query(Track).filter(Track.shazam_id == i['shazam_id']).first().id
        else:
            i['db_id'] = 0

    return render_template('charts.html', top=top, country=country_list[country])


@app.route('/recognize/track/<int:track_id>')
@app.route('/charts/track/<int:track_id>')
@app.route('/track/<int:track_id>')
def track_info(track_id):
    """ Вернуть страницу с информацией о треке """

    link = '12412412515'
    # Если трек не удалось распознать, то ничего не отправляем на вывод:
    if track_id == 0:
        return render_template('track.html')
    track = db_sess.query(Track).filter(Track.id == track_id).first()
    return render_template('track.html', track=track, link=link)


@app.route('/similiar/track/<int:track_id>')
def similiar_songs(track_id):
    """ Вернуть страницу с похожими на track_id песнями """
    return render_template('similiar_songs.html')


@app.route('/artist/track/<int:track_id>')
def about_artist(track_id):
    """ Вернуть страницу с информацией об исполнителе трека """
    return render_template('about_artist.html')


@app.route('/library')
def user_library():
    """ Распознанные песни """
    if current_user.is_authenticated:
        library = list()
        recognized = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id).all()

        for i in recognized:
            track = db_sess.query(Track).filter(Track.id == i.track_id).first()
            library.append((track, i))

        return render_template('library.html', library=reversed(library))
    return render_template('library.html')


@app.route('/delete/track/<int:track_id>', methods=["GET"])
def delete_track(track_id):
    track_to_delete = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                       Recognized.id == track_id).first()
    print(track_to_delete, '----------')
    db_sess.delete(track_to_delete)
    db_sess.commit()

    return redirect('/library')


@app.route('/featured')
def featured():
    featured_library = list()
    featured_tracks = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                       Recognized.is_favourite == 1).all()

    for i in featured_tracks:
        track = db_sess.query(Track).filter(Track.id == i.track_id).first()
        featured_library.append((track, i))

    return render_template('library.html', library=reversed(featured_library))


@app.route('/feature/track/<int:track_id>', methods=["GET"])
def feature_track(track_id):
    track = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                             Recognized.id == track_id).first()
    if not track.is_favourite:
        track.is_favourite = 1
    else:
        track.is_favourite = 0

    db_sess.commit()
    return redirect('/library')


if __name__ == '__main__':
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()
    app.run(debug=True)
