# Модули для работы с Flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request, url_for
from urllib.parse import urlparse
import asyncio

# Обработчики ShazamAPI
from data.audio_handlers.similiar_songs_handler import get_similiar_songs
from data.audio_handlers.about_artist_handler import get_artist_info
from data.audio_handlers.recognize_handler import recognize_song
from data.audio_handlers.charts_handler import charts_handler

# Форма регистрации и авторизации
from data.forms.user_change_password_form import ChangePasswordForm
from data.forms.delete_profile_form import DeleteProfileForm
from data.forms.register_form import RegisterForm
from data.forms.login_form import LoginForm
from data.forms.user_form import UserForm

# ORM-модели
from data.ORM import db_session
from data.ORM.recognized import Recognized
from data.ORM.artist import Artist
from data.ORM.track import Track
from data.ORM.user import User

# Константы и системные функции
from data.system_files.image_downloader import download_image_handler
from data.system_files.constants import *

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

@app.errorhandler(401)
@app.errorhandler(404)
def page_error_code(e):
    return render_template('handlers/error_handler.html', error_status=e)


@app.route('/', methods=["GET", "POST"])
def main():
    """ Главная страница """
    users = db_sess.query(User).all()
    active_users = list()

    users = list(sorted(users, key=lambda u: len(u.unique.split('&')), reverse=True))

    for u in users[:3]:
        user_library = db_sess.query(Recognized).filter(Recognized.user_id == u.id).all()

        user_info = dict()
        user_info['name'] = u.name
        user_info['surname'] = u.surname

        if u.gender == 'Мужской':
            user_info['background'] = url_for('static', filename='img/user_profile/man.png')
        else:
            user_info['background'] = url_for('static', filename='img/user_profile/woman.png')
        user_info['total'] = len(u.unique.split('&')) - 1
        user_info['in_library'] = len(user_library)

        active_users.append(user_info)
    return render_template('nav_pages/main.html', active_users=active_users)


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
        if any([len(form.password.data) < 9, form.password.data.isdigit()]):
            return render_template('/authentication_pages/register.html', title='Регистрация',
                                   message="Пароль содержит менее 9 символов или содержит только цифры",
                                   form=form)

        if form.password.data != form.password_again.data:
            return render_template('/authentication_pages/register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")

        # Создаём сессию, проверяем, существуют ли введённые пользователем данные в БД;
        # Если данные уже есть в базе, то отправляем соответствующее сообщение,
        # иначе - продолжаем процесс регистрации:
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('/authentication_pages/register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        # Создание объекта класса пользователя (User):
        user = User()
        user.email = form.email.data
        user.surname = form.surname.data
        user.name = form.name.data
        user.gender = form.gender.data

        # Шифруем пароль пользователя и регистрируем его:
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        # Отправляем пользователя на страницу для авторизации:
        return redirect('/login')

    # Отображение страницы регистрации:
    return render_template('/authentication_pages/register.html', title='Регистрация', form=form)


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
        return render_template('/authentication_pages/login.html', message="Неправильный логин или пароль", form=form)

    # Отображение страницы авторизации:
    return render_template('/authentication_pages/login.html', title='Авторизация', form=form)


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
        background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
        return render_template('/nav_pages/recognize.html', background=background)

    # Если пользователь отправил файл на распознание, то возвращаем пользователю информацию о распознанном треке:
    elif request.method == "POST":
        background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')

        # Загружаем отправленный пользователем файл, если пользователь ничего не отправил - перезагружаем страницу:
        f = request.files['file']
        if not f.filename:
            return render_template('/nav_pages/recognize.html', message='Вы не отправили файл', background=background)

        file_path = 'static/music/' + identifier(format_='.mp3')
        f.save(file_path)

        # Распознавание песни:
        track_data = recognize_song(file_path)
        os.remove(file_path)
        # Если программа не смогла определить трек, то уведомляем пользователя об этом:
        if track_data is None:
            return redirect('/recognize/track/0')

        # Если определение прошло успешно, то обрабатываем полученную информацию и формируем ответ:
        # Берём данные о треке:
        track_key, shazam_id, artist_id, track_title, band, background = track_data

        # Проверяем, существует ли распознанный трек в БД:
        existing = db_sess.query(Track).filter(Track.shazam_id == shazam_id).first()
        background_to_download = []

        # Если трека ещё нет в БД, то записываем информацию о нём,
        # а иначе - увеличиваем количество его распознаний:
        if not existing:
            track = Track()
            track.track_key = track_key
            track.shazam_id = shazam_id
            track.artist_id = artist_id
            track.track = track_title
            track.band = band

            if background == UNKNOWN_SONG:
                track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            else:
                filename = identifier(format_=".png")
                track.background = url_for('static', filename=f'img/track/{filename}')
                background_to_download.append([filename, background])

            db_sess.add(track)
            db_sess.commit()
            track_id = track.id
            asyncio.run(download_image_handler(background_to_download, 'track'))
        else:
            existing.popularity += 1
            track_id = existing.id
            db_sess.commit()

        # Если пользователь авторизован, то записываем информацию о
        # распознанном треке в его библиотеку:
        if current_user.is_authenticated:

            # Но если данный трек уже распознан, то перезаписываем информацию о нём:
            already_recognized = db_sess.query(Recognized).filter(
                Recognized.track_id == track_id,
                Recognized.user_id == current_user.id
            ).first()

            if already_recognized:
                db_sess.delete(already_recognized)

            recognized = Recognized()
            recognized.user_id = current_user.id
            recognized.track_id = track_id
            recognized.is_favourite = False

            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user_unique_total = user.unique.split('&')

            if str(track_id) not in user_unique_total:
                user.unique += f'{track_id}&'
                user.unique_total += 1

            db_sess.add(recognized)
            db_sess.commit()

        # Обновляем страницу:
        return redirect(f'/recognize/track/{track_id}')


@app.route('/charts/<country>/<genre>')
@app.route('/charts/<country>')
@app.route('/charts')
def charts(country=None, genre=None):
    """ Данная функция позволяет пользователю ознакомиться с мировым хит-парадом песен """

    # Возвращаем мировой топ, если не введены параметры в адрес:
    if country is None and genre is None:
        return redirect('/charts/world')

    data = charts_handler(country=country, genre=genre)
    background_to_download = list()
    top = list()

    for i in data:
        if 'shazam_id' in i:
            existing = db_sess.query(Track).filter(Track.shazam_id == i['shazam_id']).first()

            if not existing:
                track = Track()
                track.track_key = i['track_key']
                track.shazam_id = i['shazam_id']
                track.artist_id = i['artist_id']
                track.track = i['track']
                track.band = i['band']
                track.popularity = 0

                if i['background'] == UNKNOWN_SONG:
                    track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
                else:
                    filename = identifier(format_=".png")
                    track.background = url_for('static', filename=f'img/track/{filename}')
                    background_to_download.append([filename, i['background']])

                db_sess.add(track)
                db_sess.commit()
                top.append(track)

            else:
                top.append(db_sess.query(Track).filter(Track.shazam_id == i['shazam_id']).first())
        else:
            none_track = Track()
            none_track.id = 0
            none_track.track_key = 0
            none_track.shazam_id = 0
            none_track.artist_id = 0
            none_track.track = i['track']
            none_track.band = i['band']
            none_track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            none_track.popularity = 0
            top.append(none_track)

    if genre is None:
        genre = 'Все жанры'

    available_genres = AVAILABLE_GENRES[country]

    if background_to_download:
        asyncio.run(download_image_handler(background_to_download, 'track'))
    return render_template('/nav_pages/charts.html', top=top, available_genres=available_genres,
                           country=country_list[country], country_code=country, genres_list=genres_list,
                           genre_type=genres_list[genre])


@app.route('/recognize/track/<int:track_id>')
@app.route('/charts/track/<int:track_id>')
@app.route('/track/<int:track_id>')
def track_info(track_id):
    """ Вернуть страницу с информацией о треке """

    o = urlparse(request.base_url)
    hostname = o.hostname

    link = f'{o.netloc}/track/{track_id}'
    # Если трек не удалось распознать, то ничего не отправляем на вывод:
    if track_id == 0:
        return render_template('/information_pages/track.html')

    track = db_sess.query(Track).filter(Track.id == track_id).first()
    return render_template('/information_pages/track.html', track=track, link=link)


@app.route('/similiar/track/<int:track_id>')
def similiar_songs(track_id):
    """ Вернуть страницу с похожими на track_id песнями """
    track_owner = db_sess.query(Track).filter(Track.id == track_id).first()
    track_key = track_owner.track_key

    if not track_key:
        return render_template('/information_pages/similiar_songs.html')

    songs = get_similiar_songs(track_key)
    similiar_tracks = list()

    for i in songs:
        background_to_download = []

        track_key, track_shazam_id, artist_id, track_title, band, background = i
        is_track_in_db = db_sess.query(Track).filter(Track.shazam_id == track_shazam_id).first()

        if not is_track_in_db:
            track = Track()
            track.track_key = track_key
            track.shazam_id = track_shazam_id
            track.artist_id = artist_id
            track.track = track_title
            track.band = band

            if background == UNKNOWN_SONG:
                track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            else:
                filename = identifier(format_=".png")
                track.background = url_for('static', filename=f'img/track/{filename}')
                background_to_download.append([filename, background])

            db_sess.add(track)
            db_sess.commit()
            similiar_tracks.append(track)
        else:
            track = is_track_in_db
            similiar_tracks.append(track)

        asyncio.run(download_image_handler(background_to_download, 'track'))
    # В список может загрузиться несколько одинаковых песен, поэтому, избавляемся от дубликатов:
    similiar_tracks = list(set(similiar_tracks))
    return render_template('/information_pages/similiar_songs.html', track_owner=track_owner,
                           similiar_tracks=similiar_tracks)


@app.route('/artist/track/<int:track_id>')
def track_to_artist(track_id):
    track = db_sess.query(Track).filter(Track.id == track_id).first()
    artist_shazam_id = track.artist_id
    return redirect(f'/artist/{artist_shazam_id}')


@app.route('/artist/<int:artist_id>')
def about_artist(artist_id):
    """ Вернуть страницу с информацией об исполнителе трека """
    artist_shazam_id = artist_id

    o = urlparse(request.base_url)
    hostname = o.hostname
    link = f'{o.netloc}/artist/{artist_shazam_id}'

    artist_existing = db_sess.query(Artist).filter(Artist.shazam_id == artist_shazam_id).first()

    if not artist_existing:
        background_to_download = []

        try:
            all_artist_info = get_artist_info(artist_shazam_id)
        except KeyError:
            return render_template('/information_pages/about_artist.html')

        artist_shazam_id, artist_title, genre, background = all_artist_info[0][:4]
        artist = Artist()
        artist.shazam_id = artist_shazam_id
        artist.artist = artist_title
        artist.genre = genre

        if background == UNKNOWN_SONG:
            artist.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
        else:
            filename = identifier(format_=".png")
            artist.background = url_for('static', filename=f'img/artist/{filename}')
            background_to_download.append([filename, background])

        db_sess.add(artist)
        db_sess.commit()
        asyncio.run(download_image_handler(
            background_to_download, 'artist'))

    artist = db_sess.query(Artist).filter(Artist.shazam_id == artist_shazam_id).first()
    best_artist_tracks = get_artist_info(artist_shazam_id)[1]
    best_tracks = list()
    background_to_download = []
    for i in best_artist_tracks:
        track_shazam_id, track_title, band, background = i
        is_track_in_db = db_sess.query(Track).filter(Track.shazam_id == track_shazam_id).first()

        if not is_track_in_db:
            track = Track()
            track.track_key = 0  # ShazamAPI не предоставляет ключ для лучших песен артиста...
            track.shazam_id = track_shazam_id
            track.artist_id = artist_shazam_id
            track.track = track_title
            track.band = band

            if background == UNKNOWN_SONG:
                track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            else:
                filename = identifier(format_=".png")
                track.background = url_for('static', filename=f'img/track/{filename}')
                background_to_download.append([filename, background])

            db_sess.add(track)
            db_sess.commit()
            best_tracks.append(track)
        else:
            track = is_track_in_db
            best_tracks.append(track)

    all_artist_tracks = db_sess.query(Track).filter(Track.artist_id == artist_shazam_id).all()
    platform_tracks = len(all_artist_tracks)

    asyncio.run(download_image_handler(background_to_download, 'track'))
    return render_template('/information_pages/about_artist.html', artist=artist, best_tracks=best_tracks[:3],
                           platform_tracks=platform_tracks, all_tracks=all_artist_tracks, link=link)


@app.route('/library')
def user_library():
    """ Распознанные песни """
    if current_user.is_authenticated:
        library = list()
        recognized = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id).all()

        for i in recognized:
            track = db_sess.query(Track).filter(Track.id == i.track_id).first()
            library.append((track, i))

        return render_template('/user_pages/library.html', library=reversed(library))
    return render_template('/user_pages/library.html')


@app.route('/delete/track/<int:track_id>', methods=["GET"])
def delete_track(track_id):
    track_to_delete = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                       Recognized.id == track_id).first()
    db_sess.delete(track_to_delete)
    db_sess.commit()

    return redirect('/library')


@app.route('/featured')
def featured():
    if current_user.is_authenticated:
        featured_library = list()
        featured_tracks = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                           Recognized.is_favourite == 1).all()

        for i in featured_tracks:
            track = db_sess.query(Track).filter(Track.id == i.track_id).first()
            featured_library.append((track, i))

        return render_template('/user_pages/library.html', library=reversed(featured_library))
    return render_template('/user_pages/library.html')


@app.route('/feature/track/<int:track_id>', methods=["GET"])
def feature_track(track_id):
    if current_user.is_authenticated:
        track = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                 Recognized.id == track_id).first()
        if not track.is_favourite:
            track.is_favourite = 1
        else:
            track.is_favourite = 0

        db_sess.commit()
        return redirect('/library')
    return redirect('/featured')

@app.route('/cabinet')
def cabinet():
    if current_user.is_authenticated:
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user_unique_total = len(user.unique.split('&')) - 1
        return render_template('/user_pages/cabinet.html', rec_count=user_unique_total)
    return render_template('/user_pages/cabinet.html')


@app.route('/cabinet/edit', methods=['GET', 'POST'])
def edit_cabinet():
    form = UserForm()
    if current_user.is_authenticated:
        if request.method == "GET":
            form.email.data = current_user.email
            form.surname.data = current_user.surname
            form.name.data = current_user.name

        if form.validate_on_submit():
            db_sess = db_session.create_session()
            is_user_already_exists = db_sess.query(User).filter(User.email == form.email.data,
                                                                User.email != current_user.email).first()
            if is_user_already_exists:
                return render_template('/user_pages/cabinet_edit.html', form=form,
                                       message="Такой пользователь уже существует")

            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.email = form.email.data
            user.surname = form.surname.data
            user.name = form.name.data
            user.gender = form.gender.data
            db_sess.commit()
            return redirect('/cabinet')
        return render_template('/user_pages/cabinet_edit.html', form=form)
    return render_template('/user_pages/cabinet_edit.html')


@app.route('/cabinet/change-password', methods=['GET', 'POST'])
def edit_password():
    form = ChangePasswordForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            db_sess = db_session.create_session()

            current_password = form.current_password.data
            new_password = form.new_password.data
            repeat_password = form.repeat_password.data

            if not current_user.check_password(current_password):
                return render_template('/user_pages/change_password.html', form=form,
                                       message='Вы указали неверный пароль')

            if new_password != repeat_password:
                return render_template('/user_pages/change_password.html', form=form,
                                       message="Введённые пароли не совпадают")

            if any([len(new_password) < 9, new_password.isdigit()]):
                return render_template('/user_pages/change_password.html', form=form,
                                       message="Пароль содержит менее 9 символов или содержит только цифры")

            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.set_password(new_password)
            db_sess.commit()

            return render_template('/user_pages/change_password.html', form=form, message='Пароль успешно изменён')
        return render_template('/user_pages/change_password.html', form=form)
    return render_template('/user_pages/change_password.html')


@app.route('/cabinet/delete_profile', methods=['GET', 'POST'])
def delete_profile():
    form = DeleteProfileForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()

            email = form.email.data
            password = form.password.data
            repeat_password = form.repeat_password.data
            confirm = form.confirm.data

            if current_user.email != email:
                return render_template('/user_pages/delete_profile.html', form=form,
                                       message='Неправильно введена электронная почта')

            if not user.check_password(password):
                return render_template('/user_pages/delete_profile.html', form=form,
                                       message='Вы указали неправильный пароль')

            if password != repeat_password:
                return render_template('/user_pages/delete_profile.html', form=form,
                                       message='Пароли не совпадают')
            if not confirm:
                return render_template('user_pages/delete_profile.html', form=form,
                                       message='Вы не нажали на галочку')

            recognized_by_user = db_sess.query(Recognized).filter(Recognized.user_id == user.id).all()

            for r in recognized_by_user:
                db_sess.delete(r)
            db_sess.delete(user)
            db_sess.commit()
            return redirect('/login')
        return render_template('/user_pages/delete_profile.html', form=form)
    return render_template('/user_pages/delete_profile.html')


if __name__ == '__main__':
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app.run(debug=True)
