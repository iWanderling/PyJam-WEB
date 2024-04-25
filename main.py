# Модули для работы с Flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, redirect, request, url_for
from flask_restful import Api, abort

# Библиотека для работы с функцией "Поделиться"
from urllib.parse import urlparse
import asyncio  # Asyncio - для асинхронной загрузки изображений

# Обработчики ShazamAPI
from data.audio_handlers.similiar_songs_handler import get_similiar_songs
from data.audio_handlers.about_artist_handler import get_artist_info
from data.audio_handlers.recognize_handler import recognize_song_handler
from data.audio_handlers.charts_handler import charts_handler

# Форма регистрации и авторизации
from data.forms.user_change_password_form import ChangePasswordForm
from data.forms.delete_profile_form import DeleteProfileForm
from data.forms.register_form import RegisterForm
from data.forms.login_form import LoginForm
from data.forms.user_form import UserForm

# API-формы:
from data.api import artist_json_api
from data.api import track_json_api

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
app.config['SECRET_KEY'] = 'FFFFF0-JHKMQ1-KRMB89-KLLLVV-ZZHMN5'  # Секретный ключ

# Инициализация объекта класса Api, для работы с REST-API библиотеки Flask:
api = Api(app)

# Добавление API треков:
api.add_resource(track_json_api.TrackJsonAPI, '/api/v1/track/<int:track_id>')
api.add_resource(track_json_api.TrackAllJsonAPI, '/api/v1/track')

# Добавление API исполнителей:
api.add_resource(artist_json_api.ArtistJsonAPI, '/api/v1/artist/<int:artist_id>')
api.add_resource(artist_json_api.ArtistAllJsonAPI, '/api/v1/artist')

# Инициализация объекта LoginManager, функции для загрузки пользователя:
login_manager = LoginManager()
login_manager.init_app(app)


def dt_prefix():
    """ DT_Prefix -> DarkTheme_Prefix. Функция для обработки выбранной пользователем темы.
        Prefix - префикс для HTML-файла. Если у пользователя тёмная тема, то будет использоваться префикс _dark,
                 иначе, префикс будет пустым и отобразиться стандартная страница.
        Пример: nav_pages/main{dt_prefix()}.html """
    if current_user.is_authenticated:
        if current_user.is_dark_mode:
            return '_dark'
    return ''


@login_manager.user_loader
def load_user(user_id):
    """ Загрузка пользователя """
    return db_sess.query(User).get(user_id)


@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def page_error_code(e):
    """ Обработчики ошибок на странице """
    return render_template(f'handlers/error_handler{dt_prefix()}.html', error_status=f'Ошибка: {e}')


def is_admin():
    """ Проверка: является ли текущий на сайте пользователь администратором """
    is_admin_ = current_user.is_authenticated and current_user.id == 1
    if not is_admin_:
        return abort(403)


@app.route('/rules')
def rules():
    """ Страница с основными правилами платформы """
    return render_template(f'/information_pages/rules{dt_prefix()}.html')


@app.route('/', methods=["GET", "POST"])
def main():
    """  Главная страница платформы PyJam.
         Данная страница отображает основную статистику по всему сайту,
         а также топы: самых активных пользователей, самых популярных треков, самых популярных исполнителей. """

    # Загрузка информации о зарегистрированных пользователях:
    users = list(sorted(db_sess.query(User).all(), key=lambda us: len(us.unique.split('&')), reverse=True))

    # Загрузка информации о библиотеке сайта:
    big_library = db_sess.query(Recognized).all()

    # Загрузка информации обо всех загруженных на сайт треков:
    tracks = list(sorted(db_sess.query(Track).all(), key=lambda t: t.popularity, reverse=True))

    # Загрузка статистики обо всех зарегистрированных пользователях на платформе,
    # загрузка топа самых активных пользователей:
    all_users = len(users)  # количество зарегистрированных пользователей
    active_users = list()  # топ активных пользователей хранится в этом списке

    # Загружаем информацию для топа (берём первых трёх самых активных пользователей)
    for u in users:
        if u.id > 1:
            user_library = db_sess.query(Recognized).filter(Recognized.user_id == u.id).all()
            user_info = dict()
            user_info['id'] = u.id
            user_info['name'] = u.name
            user_info['surname'] = u.surname
            user_info['background'] = u.background
            user_info['total'] = len(u.unique.split('&')) - 1
            user_info['in_library'] = len(user_library)
            active_users.append(user_info)
        if len(active_users) == 3:
            break

    # Загрузка статистики обо всех треках, находящихся в библиотеках у пользователей,
    # загрузка статистики обо всех треках, которые избраны у пользователей в библиотеках:
    in_library_tracks = len(big_library)
    in_feature_tracks = len([rec for rec in big_library if rec.is_favourite == 1])

    # Всего распознано треков, треков на платформе, исполнителей на платформе (суммарно)
    recognized_total = sum([track.popularity for track in tracks])
    track_on_platform = len(tracks)
    artist_on_platform = len(set([t.artist_id for t in tracks]))

    # Загрузка информации о самых популярных треках на платформе (по количеству распознаний):
    most_popular_tracks = []
    for track in tracks[:3]:
        most_popular_tracks.append(track)

    # Загрузка информации о самых популярных исполнителях на платформе (по количеству распознанных треков):
    most_popular_artists = []
    best_artists_info = dict()

    for track in tracks:
        artist_shazam_id = track.artist_id  # берём Shazam_Id исполнителя из трека:
        if artist_shazam_id not in best_artists_info:
            best_artists_info[artist_shazam_id] = [0, 0]  # подсчитываем количество распознаний и треков на платформе
        best_artists_info[artist_shazam_id][0] += 1  # счётчик на платформе
        best_artists_info[artist_shazam_id][1] += track.popularity  # счётчик распознаний всех треков исполнителя
    if 0 in best_artists_info:
        del best_artists_info[0]

    # После обработки информации об исполнителях, загружаем ключи трёх самых популярных исполнителей:
    best_artist_shazam_ids = list(sorted(best_artists_info.keys(),
                                         key=lambda x: best_artists_info[x], reverse=True))[:3]

    # А дальше - загружаем информацию о них, а затем - выводим все данные:
    for artist_shazam_id in best_artist_shazam_ids:
        is_artist_on_platform = db_sess.query(Artist).filter(Artist.shazam_id == artist_shazam_id).first()

        # Если исполнителя нет в БД - загружаем информацию о нём и добавляем в БД,
        # иначе - просто берём информацию из БД:
        if not is_artist_on_platform:
            background_to_download = []  # список для загрузки изображений с интернета
            artist_info = get_artist_info(artist_shazam_id)[0]
            artist_id, artist_title, artist_genre, artist_background = artist_info

            artist = Artist()
            artist.shazam_id = artist_shazam_id
            artist.artist = artist_title
            artist.genre = artist_genre

            if artist_background == UNKNOWN_SONG:
                artist.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            else:
                filename = identifier(format_=".png")
                artist.background = url_for('static', filename=f'img/artist/{filename}')
                background_to_download.append([filename, artist_background])

            # Добавляем исполнителя, коммитим изменения:
            db_sess.add(artist)
            db_sess.commit()

            # Добавляем изображение в очередь на загрузку:
            most_popular_artists.append([artist, best_artists_info[artist_shazam_id]])
            asyncio.run(download_image_handler(
                background_to_download, 'artist'))
        else:
            most_popular_artists.append([is_artist_on_platform, best_artists_info[artist_shazam_id]])

    # Отображаем статистику, если хотя-бы одна из позиций - ненулевая (такое может быть в самом начале работы сайта)
    show_statistics = any([all_users, recognized_total, in_library_tracks, in_feature_tracks,
                           track_on_platform, artist_on_platform])

    # Отображаем информацию:
    return render_template(f'nav_pages/main{dt_prefix()}.html',
                           all_users=all_users, active_users=active_users,
                           show_statistics=show_statistics, recognized_total=recognized_total,
                           library_tracks=in_library_tracks, feature_tracks=in_feature_tracks,
                           track_on_platform=track_on_platform, artist_on_platform=artist_on_platform,
                           most_popular_tracks=most_popular_tracks, most_popular_artists=most_popular_artists)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    """ Страница для регистрации пользователей.
        Содержит специальную форму RegisterForm, в которой представлены все необходимые поля для
        успешной регистрации пользователя. Необходимо заполнить все поля.
        Пользователь проходит регистрацию, только если соблюдены все условия, которые перечислены ниже:
        1. Пароль содержит от 9 символов и содержит не только цифры;
        2. Поля "Пароль" и "Повторите пароль" совпадают;
        3. Имя и фамилия пользователя содержат до 41 символа;
        4. E-Mail пользователя ещё не лежит в БД, либо же пользователь ещё не зарегистрировался на платформе;
    """

    # Создание объекта регистрационной формы (RegisterForm). Форма обрабатывает
    # введённые пользователем данные, и если все данные введены верно,
    # то регистрирует пользователя в системе:
    form = RegisterForm()

    # Обработка нажатия на кнопку регистрации (ДАЛЕЕ - УСЛОВИЯ РЕГИСТРАЦИИ):
    if form.validate_on_submit():
        # 1. Проверка пароля на надёжность:
        if any([len(form.password.data) < 9, form.password.data.isdigit()]):
            return render_template(f'/authentication_pages/register{dt_prefix()}.html', title='Регистрация',
                                   message="Пароль содержит менее 9 символов или содержит только цифры",
                                   form=form)

        # 2. Проверка полей с паролями на совпадение:
        if form.password.data != form.password_again.data:
            return render_template(f'/authentication_pages/register{dt_prefix()}.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")

        # 3. Проверка имени и фамилии:
        if len(form.name.data) > 41 or len(form.surname.data) > 41:
            return render_template(f'/authentication_pages/register{dt_prefix()}.html', title='Регистрация',
                                   form=form,
                                   message="Слишком длинное имя / фамилия")

        # 4. Если данные уже есть в базе, то отправляем соответствующее сообщение,
        # иначе - продолжаем процесс регистрации:
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(f'/authentication_pages/register{dt_prefix()}.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        # Создание объекта класса пользователя (User):
        user = User()
        user.email = form.email.data
        user.surname = form.surname.data
        user.name = form.name.data
        user.gender = form.gender.data

        # Выбранный пол определяет, какое стоковое изображение загрузится в профиль пользователя (Мужское/Женское)
        if user.gender == 'Мужской':
            user.background = url_for('static', filename=MAN_PROFILE_PICTURE)
        else:
            user.background = url_for('static', filename=WOMAN_PROFILE_PICTURE)

        # Шифруем пароль пользователя и регистрируем его:
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        # Отправляем пользователя на страницу для авторизации:
        return redirect('/login')

    # Отображение страницы регистрации:
    return render_template(f'/authentication_pages/register{dt_prefix()}.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Страница для авторизации пользователя.
        Содержит специальную форму LoginForm, в которой представлены все необходимые
        поля для успешной авторизации пользователя. Необходимо заполнить все поля.
        Для успешной регистрации необходимо указать корректные E-Mail и пароль,
        которые были указаны пользователем при регистрации. """

    # Создание объекта формы для входа в аккаунт (LoginForm). Форма обрабатывает введённые пользователем данные,
    # и если все данные введены верно, то авторизует пользователя в системе:
    form = LoginForm()

    # Обработка нажатия на кнопку входа в аккаунт:
    if form.validate_on_submit():

        # Создание сессии, обработка введённых пользователем данных
        # Незамедлительно авторизуем пользователя при успешном прохождении авторизации:
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        # Авторизация:
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/cabinet")

        # Если пользователь ввёл некорректные данные, то выводим соответствующее сообщение:
        return render_template(f'/authentication_pages/login{dt_prefix()}.html',
                               message="Неправильный логин или пароль", form=form)

    # Отображение страницы авторизации:
    return render_template(f'/authentication_pages/login{dt_prefix()}.html', title='Авторизация', form=form)


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

        После распознания трек записывается в специальную таблицу в БД, чтобы в дальнейшем можно было
        поделиться треком и быстро отобразить его в библиотеке АВТОРИЗОВАННОГО пользователя,
        а также на остальных страницах платформы. """

    try:
        # Если пользователь ничего не отправил - возвращаем обычную страницу:
        if request.method == "GET":
            background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
            return render_template(f'/nav_pages/recognize_song{dt_prefix()}.html', background=background)

        # Если пользователь отправил файл на распознание, то возвращаем пользователю информацию о распознанном треке:
        elif request.method == "POST":
            background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')

            # Загружаем отправленный пользователем файл, если пользователь ничего не отправил - перезагружаем страницу:
            f = request.files['file']
            if not f.filename:
                return render_template(f'/nav_pages/recognize_song{dt_prefix()}.html',
                                       message='Вы не отправили файл', background=background)

            # Создаём уникальный путь для аудиофайла, которое мы будем загружать,
            # а затем сохраняем файл по указанному пути. После система его распознаёт и автоматически удаляет файл:
            file_path = 'static/music/' + identifier(format_='.mp3')
            f.save(file_path)

            # Распознавание песни и удаление файла:
            track_data = recognize_song_handler(file_path)
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

                # Загружаем изображение (обложку трека) с помощью асинхронной функции.
                # Сохраняем путь к обложке трека в специальном поле в БД [Tracks]
                if background == UNKNOWN_SONG:
                    track.background = url_for('static', filename=f'img/system/{UNKNOWN_SONG}')
                else:
                    filename = identifier(format_=".png")
                    track.background = url_for('static', filename=f'img/track/{filename}')
                    background_to_download.append([filename, background])

                # Добавляем трек в БД и коммитим изменения:
                db_sess.add(track)
                db_sess.commit()
                track_id = track.id

                # Загружаем изображение:
                asyncio.run(download_image_handler(background_to_download, 'track'))
            else:
                existing.popularity += 1
                track_id = existing.id
                db_sess.commit()

            # Если пользователь авторизован, то записываем информацию о распознанном треке в его библиотеку:
            if current_user.is_authenticated:

                # Но если данный трек уже распознан, то перезаписываем информацию о нём:
                already_recognized = db_sess.query(Recognized).filter(
                    Recognized.track_id == track_id, Recognized.user_id == current_user.id).first()

                # Если трек уже распознан, то перезаписываем его в БД, сохраняя данные об избранности:
                do_favor = 0
                if already_recognized:
                    if already_recognized.is_favourite:
                        do_favor = 1

                    db_sess.delete(already_recognized)

                recognized = Recognized()
                recognized.user_id = current_user.id
                recognized.track_id = track_id
                recognized.is_favourite = do_favor

                # Увеличиваем количество распознанных пользователем уникальных треков, если этот
                # трек он распознал впервые:
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                user_unique_total = user.unique.split('&')

                if str(track_id) not in user_unique_total:
                    user.unique += f'{track_id}&'
                    user.unique_total += 1

                # Сохраняем изменения:
                db_sess.add(recognized)
                db_sess.commit()

            # Обновляем страницу:
            return redirect(f'/recognize/track/{track_id}')
    except Exception as e:
        status_error = e
        return render_template(f'/nav_pages/recognize_song{dt_prefix()}.html',
                               message='Произошла ошибка. Попробуйте ещё раз!')


@app.route('/charts/<country>/<genre>')
@app.route('/charts/<country>')
@app.route('/charts')
def charts(country=None, genre=None):
    """ Данная функция позволяет пользователю ознакомиться с хит-парадом* песен в следующих категориях:
        1. Мировые хиты;
        2. Хиты определённой страны, которую можно выбрать в фильтрах страницы;
        3. Хиты в определённом жанре, который можно выбрать в фильтрах страницы; сочетается с ост. фильтрами;

        Страница производит автоматическое добавление треков в БД, а также загружает все изображения в
        специальную папку с помощью асинхронной функции image_downloader.

        * - по версии Shazam.
    """

    # Возвращаем мировой топ, если не введены параметры в адрес:
    if country is None and genre is None:
        return redirect('/charts/world')

    # Получаем информацию с помощью ShazamAPI (Shazamio), и если ошибки не возникает - возвращаем хит-парад!
    try:
        # Обрабатываем запрос, получаем данные:
        data = charts_handler(country=country, genre=genre)
        background_to_download = list()  # создаём список для загрузки изображений
        top = list()  # создаём список, в котором будут храниться все хиты

        # Пробегаемся по каждому элементу полученных данных, формируя из них хит-парад,
        # при этом добавляя каждый элемент в БД, если его в ней ещё нет:
        for i in data:
            # Если API предоставил информацию, то загружаем её в БД, иначе - просто отображаем её на странице:
            if 'shazam_id' in i:
                existing = db_sess.query(Track).filter(Track.shazam_id == i['shazam_id']).first()

                if not existing:
                    track = Track()
                    track.track_key = i['track_key']
                    track.shazam_id = i['shazam_id']
                    track.artist_id = i['artist_id']
                    track.track = i['track']
                    track.band = i['band']

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
                top.append(none_track)

        # Если не выбрал жанр, то в фильтрах указываем текст: "Все жанры":
        if genre is None:
            genre = 'Все жанры'

        # Доступные жанры для определённой страны:
        available_genres = AVAILABLE_GENRES[country]

        # Загружаем изображения, которые были добавлены в очередь на загрузку:
        if background_to_download:
            asyncio.run(download_image_handler(background_to_download, 'track'))

        # Возвращаем информацию:
        return render_template(f'/nav_pages/charts{dt_prefix()}.html', top=top, available_genres=available_genres,
                               country=country_list[country], country_code=country, genres_list=genres_list,
                               genre_type=genres_list[genre])

    # Ошибка всегда происходит лишь на серверной стороне ShazamAPI, поэтому, если она происходит,
    # то высылаем пользователю сообщение "о неполадках на сервере".
    # ОБНОВЛЕНИЕ: в случае ошибки на стороне ShazamAPI, реализована "запасная страница" со всеми треками на
    # платформе и статистикой по ним:
    except Exception as e:
        status_error = e
        return redirect('/commons/tracks')


@app.route('/commons/<page_type>')
def commons(page_type):
    """ Вторая страница чартов, способная заменить первую в случае сбоя в работе SHAZAMAPI.
        Отображает информацию обо всех треках, существующих на платформе. Каждый трек
        является ссылкой на самого себя, благодаря чему пользователь может более подробно
        изучить ту или иную песню и музыку. """

    # Фильтр Tracks: отображаем все загруженные на платформу треки:
    if page_type == 'tracks':
        tracks = sorted([t for t in db_sess.query(Track).all()], key=lambda track: track.popularity, reverse=True)
        return render_template(f'/nav_pages/commons{dt_prefix()}.html', top=tracks,
                               page_type='tracks')

    # Фильтр Artists: отображаем всех загруженных на платформу исполнителей:
    elif page_type == 'artists':
        all_artists = []

        for art in db_sess.query(Artist).all():
            # Список со всеми треками исполнителя, а также получение количества всех треков исполнителя:
            all_artist_tracks = db_sess.query(Track).filter(Track.artist_id == art.shazam_id).all()
            platform_tracks = len(all_artist_tracks)
            apt = sum([t.popularity for t in all_artist_tracks])
            all_artists.append([art, apt, platform_tracks])

        all_artists.sort(key=lambda x: x[1])
        return render_template(f'/nav_pages/commons{dt_prefix()}.html', all_artists=all_artists,
                               page_type='artists')
    return redirect('/commons/tracks')


@app.route('/recognize/track/<int:track_id>')
@app.route('/commons/track/<int:track_id>')
@app.route('/charts/track/<int:track_id>')
@app.route('/track/<int:track_id>')
def track_info(track_id):
    """ Данная страница предоставляет подробную информацию о треке, о котором хочет узнать пользователь.
        Она содержит возможность поделиться ссылкой на выбранный трек, а также предоставляет доступ к
        таким функциям, как "Похожие песни" и "Об исполнителе". """

    # Получаем ссылку на трек:
    o = urlparse(request.base_url)
    link = f'{o.netloc}/track/{track_id}'

    # Если трек не удалось распознать, то ничего не отправляем на вывод:
    if track_id == 0:
        return render_template(f'/information_pages/track{dt_prefix()}.html')

    # Иначе, находим трек и отправляем данные:
    track = db_sess.query(Track).filter(Track.id == track_id).first()
    return render_template(f'/information_pages/track{dt_prefix()}.html', track=track, link=link)


@app.route('/similiar/track/<int:track_id>')
def similiar_songs(track_id):
    """ Данная страница возвращает информацию обо всех песнях, схожих с той, что избрал пользователь
        на странице с информацией о треке. Содержание этой страницы состоит из обложки, названия
        песни и названия группы каждой похожей песни. По щелчку на название пользователь может
        просмотреть информацию о каждой похожей песне, если она содержится в БД. """

    try:
        # Получаем трек, для которого нужно найти похожие песни. Затем получаем ключ, по которому
        # будет происходить поиск необходимой информации:
        track_owner = db_sess.query(Track).filter(Track.id == track_id).first()
        track_key = track_owner.track_key

        # Если у трека нет ключа, то ничего не возвращаем:
        if not track_key:
            return render_template(f'/information_pages/similiar_songs{dt_prefix()}.html')

        # Получаем информацию обо всех похожих песнях:
        songs = get_similiar_songs(track_key)
        similiar_tracks = list()
        background_to_download = []

        # Загружаем такие песни в БД, если они ещё не находятся в ней, а затем - отображаем на странице:
        for i in songs:
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

        # В список может загрузиться несколько одинаковых песен, поэтому, избавляемся от дубликатов:
        similiar_tracks = list(set(similiar_tracks))

        # Загрузка изображений:
        asyncio.run(download_image_handler(background_to_download, 'track'))

        # Возвращаем информацию:
        return render_template(f'/information_pages/similiar_songs{dt_prefix()}.html', track_owner=track_owner,
                               similiar_tracks=similiar_tracks)
    except Exception as e:
        status_error = e
        return render_template(f'/information_pages/similiar_songs{dt_prefix()}.html')

@app.route('/artist/track/<int:track_id>')
def track_to_artist(track_id):
    """ Ссылка-трансфер на другую страницу, на которой отображена информация об исполнителе """
    try:
        track = db_sess.query(Track).filter(Track.id == track_id).first()
        artist_shazam_id = track.artist_id
        return redirect(f'/artist/shazam_id/{artist_shazam_id}')
    except Exception as e:
        status_error = e
        return render_template(f'/information_pages/about_artist{dt_prefix()}.html')

@app.route('/artist/shazam_id/<int:artist_id>')
def download_artist(artist_id):
    """ Ссылка-трансфер на другую страницу, на которой отображена информация об исполнителе.
        В отличие от функции track_to_artist, функция download_artist сначала загружает информацию
        об исполнителе в БД, и лишь тогда переадресует на страницу исполнителя. """

    # Получаем Shazam_ID исполнителя
    artist_shazam_id = artist_id

    # Проверяем, существует ли исполнитель в БД:
    artist_existing = db_sess.query(Artist).filter(Artist.shazam_id == artist_shazam_id).first()

    # Если исполнителя ещё нет в БД, то загружаем информацию о нём:
    if not artist_existing:
        background_to_download = []

        # Если получить информацию об исполнителе не удалось, то ловим ошибку и возвращаем пустую страницу с
        # соответствующим сообщением:
        try:
            all_artist_info = get_artist_info(artist_shazam_id)
        except KeyError:
            return render_template(f'/information_pages/about_artist{dt_prefix()}.html')

        # Если всё прошло успешно, то загружаем данные:
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

    # Получаем ID исполнителя в БД, а затем - производим трансфер на другую страницу:
    artist = db_sess.query(Artist).filter(Artist.shazam_id == artist_shazam_id).first()
    artist_db_id = artist.id

    # Переадресация на страницу исполнителя:
    return redirect(f'/artist/{artist_db_id}')


@app.route('/recognized/artist/<int:artist_id>')
@app.route('/commons/artist/<int:artist_id>')
@app.route('/charts/artist/<int:artist_id>')
@app.route('/artist/<int:artist_id>')
def about_artist(artist_id):
    """ Данная страница отображает краткую информацию об исполнителе, которого ищет пользователь.
        На этой странице представлены:
        1. Информация об исполнителе;
        2. Самые популярные треки исполнителя (На платформе Shazam);
        3. Все треки исполнителя на платформе.
        Также предоставлена кнопка "Поделиться исполнителем", при нажатии на которую в буфер обмена
        копируется ссылка на страницу исполнителя на платформе.
     """

    try:
        # Если artist_id == 0 (исполнитель не найден), то возвращаем пустую страницу с соответствующим сообщением,
        # иначе - продолжаем обработку информации:
        if not artist_id:
            return render_template(f'/information_pages/about_artist{dt_prefix()}.html')

        # Загружаем ссылку на исполнителя:
        o = urlparse(request.base_url)
        link = f'{o.netloc}/artist/{artist_id}'

        # Получаем информацию об исполнителе из БД:
        artist = db_sess.query(Artist).filter(Artist.id == artist_id).first()
        artist_shazam_id = artist.shazam_id

        # Список, в котором будут храниться лучшие треки исполнителя:
        best_artist_tracks = get_artist_info(artist_shazam_id)[1]
        best_tracks = list()

        # Обрабатываем информацию, по необходимости добавляем информацию о треке в БД, если его ещё не существует у нас:
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

        # Список со всеми треками исполнителя, а также получение количества всех треков исполнителя:
        all_artist_tracks = db_sess.query(Track).filter(Track.artist_id == artist_shazam_id).all()
        platform_tracks = len(all_artist_tracks)
        artist_popularity_total = sum([t.popularity for t in all_artist_tracks])

        # Загрузка изображений:
        asyncio.run(download_image_handler(background_to_download, 'track'))

        # Отображение страницы:
        return render_template(f'/information_pages/about_artist{dt_prefix()}.html',
                               artist=artist, best_tracks=best_tracks[:3], platform_tracks=platform_tracks,
                               all_tracks=all_artist_tracks, link=link, apt=artist_popularity_total)
    except Exception as e:
        status_error = e
        return render_template(f'/information_pages/about_artist{dt_prefix()}.html')


@app.route('/library')
def user_library_handler():
    """ Данная страница представляет собою виртуальную библиотеку, в которой хранится информация обо всех
        треках, что смог распознать пользователь сайта.
        Библиотека доступна только для авторизованных пользователей.

        Управление библиотекой: пользователь может удалять распознанные треки, а также добавлять их в "избранное".
        При распознании трек записывается в БД, а также обновляет собственное время распознания, перезаписывая себя.
        Каждое название трека - это ссылка, при нажатии на которую пользователь сможет более подробно изучить
        полюбившуюся им песню. """

    # Если пользователь авторизован, то отображем его личную библиотеку:
    if current_user.is_authenticated:
        library = list()
        recognized = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id).all()

        # Загружаем данные:
        for i in recognized:
            track = db_sess.query(Track).filter(Track.id == i.track_id).first()
            library.append((track, i))

        # Отправляем страницу с библиотекой
        return render_template(f'/user_pages/library{dt_prefix()}.html', library=reversed(library))

    # Отображаем пустую страницу с сообщением, если пользователь ещё не авторизовался на сайте:
    return render_template(f'/user_pages/library{dt_prefix()}.html')


@app.route('/delete/track/<int:track_id>', methods=["GET"])
def delete_track(track_id):
    """ Данная функция удаляет распознанный трек из библиотеки пользователя.
        Удалить избранный трек может только тот пользователь, которому принадлежит библиотека. """

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:
        track_to_delete = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                           Recognized.id == track_id).first()

        # Проверяем, принадлежит ли трек библиотеке пользователя. Если принадлежит - то удаляем его:
        if track_to_delete:
            db_sess.delete(track_to_delete)
            db_sess.commit()

    # Перезагружаем библиотеку:
    return redirect('/library')


@app.route('/featured')
def featured():
    """ Данная функция является фильтром. Она отображает в библиотеке только те треки, которые пользователь
        сделал избранными и что принадлежат только ему. """

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:

        # Фильтруем библиотеку, возвращаем избранные треки:
        featured_library = list()
        featured_tracks = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                           Recognized.is_favourite == 1).all()

        for i in featured_tracks:
            track = db_sess.query(Track).filter(Track.id == i.track_id).first()
            featured_library.append((track, i))

        return render_template(f'/user_pages/library{dt_prefix()}.html', library=reversed(featured_library))
    return render_template(f'/user_pages/library{dt_prefix()}.html')


@app.route('/feature/track/<int:track_id>', methods=["GET"])
def feature_track(track_id):
    """ Данная функция делает трек в библиотеке избранным, и наоборот.
        Доступна только авторизованному пользователю.
        Изменять статус трека может только пользователь, которому он принадлежит. """

    # Проверка авторизации:
    if current_user.is_authenticated:
        track = db_sess.query(Recognized).filter(Recognized.user_id == current_user.id,
                                                 Recognized.id == track_id).first()

        # Если трек принадлежит пользователю - меняем его статус и обновляем страницу:
        if track:
            if not track.is_favourite:
                track.is_favourite = 1
            else:
                track.is_favourite = 0

            db_sess.commit()
            return redirect('/library')
    return redirect('/featured')


@app.route('/cabinet', methods=['GET', 'POST'])
def cabinet():
    """ Данная страница представляет собой виртуальный "личный кабинет",
        который доступен только авторизованным пользователям.

        В личном кабинете пользователь может изменять свои личные данные,
        просматривать свою статистику, загружать изображение в свой личный профиль.

        Доступные функции:
            1. Редактировать данные -> изменить свои E-mail, имя и фамилию;
            2. Сменить пароль -> изменить свой пароль;
            3. Выйти из аккаунта;
            4.1. Удалить свой профиль -> доступно только обычным пользователям сайта;
            4.2 Кабинет администратора -> доступно только для администраторов сайта; """

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:

        # Собираем статистику пользователя, чтобы отобразить её в ЛК:
        users = db_sess.query(User).all()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        user_unique_total = len(user.unique.split('&')) - 1
        user_in_library = len(db_sess.query(Recognized).filter(Recognized.user_id == user.id).all())
        user_in_featured = len(db_sess.query(Recognized).filter(Recognized.user_id == user.id,
                                                                Recognized.is_favourite == 1).all())
        user_in_top = list(sorted(users, key=lambda u: len(u.unique.split('&')), reverse=True)).index(user) + 1

        # Если пользователь не загружает изображение в свой профиль, то отправляем статистику и доступ к функциям:
        if request.method == 'GET':
            return render_template(f'/user_pages/cabinet{dt_prefix()}.html', rec_count=user_unique_total,
                                   library_count=user_in_library, featured_count=user_in_featured,
                                   intop_position=user_in_top, date=user.date)

        # Если же он загружает изображение, то помимо вышеперечисленного обновляем изображения пользователя:
        elif request.method == 'POST':
            f = request.files['file']
            photo_filename = f.filename

            # Если пользователь не загрузил файл, но нажал на кнопку, или же он
            # отправил не изображение, то возвращаем обычную страницу:
            if not f.filename or not any([photo_filename[-4:] == '.png', photo_filename[-4:] == '.jpg']):
                return render_template(f'/user_pages/cabinet{dt_prefix()}.html', rec_count=user_unique_total,
                                       library_count=user_in_library, featured_count=user_in_featured,
                                       intop_position=user_in_top, date=user.date)

            # Иначе - загружаем файл на сервер и обновляем изображения профиля пользователя:
            file_path = 'static/img/user_profile/' + identifier(format_='.png')
            f.save(file_path)
            user.background = f'/{file_path}'
            db_sess.commit()
            return redirect('/cabinet')

    # Загружаем ЛК:
    return render_template(f'/user_pages/cabinet{dt_prefix()}.html')


@app.route('/cabinet/set_default')
def cabinet_set_default_profile():
    """ Данная функция устанавливает стандартное изображение профиля для пользователя"""

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        # Если пол пользователя - мужской, то загружаем изображение мужчины, иначе - женщины:
        if user.gender == 'Мужской':
            user.background = url_for('static', filename='img/user_profile/man.png')
        else:
            user.background = url_for('static', filename='img/user_profile/woman.png')

        # Сохраняем изменения и производим обновление страницы:
        db_sess.commit()
    return redirect('/cabinet')


@app.route('/cabinet/dark_mode')
def cabinet_set_dark_mode():
    """ Данная функция включает / выключает тёмную тему на сайте для пользователя """

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        # Включаем / выключаем тёмную тему:
        if user.is_dark_mode == 1:
            user.is_dark_mode = 0
        else:
            user.is_dark_mode = 1

        # Сохраняем изменения и производим обновление страницы:
        db_sess.commit()
        print(user.is_dark_mode)
    return redirect('/cabinet')


@app.route('/cabinet/edit', methods=['GET', 'POST'])
def edit_cabinet():
    """ Данная страница позволяет изменить пользователю свои личные данные: E-mail, имя и фамилию.
        Данные пользователя обновляются, если им соблюдены следующие условия:
        1. Новый E-Mail пользователя не используется другим пользователем на платформе;
        2. Новые имя и фамилия пользователя содержат до 41 символа. """

    # Инициализируем форму для смены данных:
    form = UserForm()

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:

        # Загружаем текущие данные пользователя в форму, для удобного изменения:
        if request.method == "GET":
            form.email.data = current_user.email
            form.surname.data = current_user.surname
            form.name.data = current_user.name

        # Если пользователь подтвердил изменения, то обрабатываем условия; если все условия соблюдены, то
        # производим обновление информации:
        if form.validate_on_submit():

            # 1. Новый E-Mail пользователя не используется другим пользователем на платформе:
            is_user_already_exists = db_sess.query(User).filter(User.email == form.email.data,
                                                                User.email != current_user.email).first()
            if is_user_already_exists:
                return render_template(f'/user_pages/cabinet_edit{dt_prefix()}.html', form=form,
                                       message="Такой пользователь уже существует")

            # 2. Новые имя и фамилия пользователя содержат до 41 символа:
            if len(form.name.data) > 41 or len(form.surname.data) > 41:
                return render_template(f'/user_pages/cabinet_edit{dt_prefix()}.html', form=form,
                                       message="Слишком длинное имя / фамилия")

            # Все условия соблюдены, значит, можем обновлять данные:
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.email = form.email.data
            user.surname = form.surname.data
            user.name = form.name.data
            user.gender = form.gender.data

            # Если пользователь ещё не загрузил своё изображение, то меняем стандартное изображение
            # в зависимости от его пола:
            if url_for('static', filename='img/user_profile/man.png') == user.background or \
                    url_for('static', filename='img/user_profile/woman.png') == user.background:
                if user.gender == 'Мужской':
                    user.background = url_for('static', filename='img/user_profile/man.png')
                else:
                    user.background = url_for('static', filename='img/user_profile/woman.png')

            # Сохраняем изменения, переводим пользователя в личный кабинет:
            db_sess.commit()
            return redirect('/cabinet')

        # Загружаем форму
        return render_template(f'/user_pages/cabinet_edit{dt_prefix()}.html', form=form)

    # Ничего не загружаем, если пользователь не авторизован:
    return render_template(f'/user_pages/cabinet_edit{dt_prefix()}.html')


@app.route('/cabinet/change-password', methods=['GET', 'POST'])
def edit_password():
    """ Данная страница позволяет пользователю изменить свой пароль.
        Пароль обновляется, если соблюдены следующие условия:
        1. Пользователь указал свой текущий пароль перед изменением;
        2. Поля "Пароль" и "Повторите пароль" совпадают;
        3. Пароль содержит от 9 символов и содержит не только цифры. """

    # Инициализация формы для смены пароля:
    form = ChangePasswordForm()

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:

        # Если пользователь подтверждает изменения, то проверяем условия, после чего обновляем пароль:
        if form.validate_on_submit():
            current_password = form.current_password.data
            new_password = form.new_password.data
            repeat_password = form.repeat_password.data

            # 1. Пользователь указал свой текущий пароль перед изменением:
            if not current_user.check_password(current_password):
                return render_template(f'/user_pages/change_password{dt_prefix()}.html', form=form,
                                       message='Вы указали неверный пароль')

            # 2. Поля "Пароль" и "Повторите пароль" совпадают:
            if new_password != repeat_password:
                return render_template(f'/user_pages/change_password{dt_prefix()}.html', form=form,
                                       message="Введённые пароли не совпадают")

            # 3. Пароль содержит от 9 символов и содержит не только цифры:
            if any([len(new_password) < 9, new_password.isdigit()]):
                return render_template(f'/user_pages/change_password{dt_prefix()}.html', form=form,
                                       message="Пароль содержит менее 9 символов или содержит только цифры")

            # Все условия пройдены - обновляем пароль:
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.set_password(new_password)
            db_sess.commit()

            # Переводим пользователя в личный кабинет:
            return render_template(f'/user_pages/change_password{dt_prefix()}.html',
                                   form=form, message='Пароль успешно изменён')

        # Загружаем форму:
        return render_template(f'/user_pages/change_password{dt_prefix()}.html', form=form)

    # Ничего не загружаем, если пользователь не авторизован:
    return render_template(f'/user_pages/change_password{dt_prefix()}.html')


@app.route('/cabinet/delete_profile', methods=['GET', 'POST'])
def delete_profile():
    """ На данной странице пользователь может удалить свой аккаунт.
        Поскольку удаление аккаунта - процесс необратимый, то и подготовка к его удалению - соответствующая.
        Чтобы удалить аккаунт, пользователь ОБЯЗАН выполнить несколько очень важных условий:
        1. Пользователь должен ввести свою электронную почту, указанную у него в профиле;
        2. Пользователь должен указать свой текущий пароль;
        3. Пользователь должен повторить свой текущий пароль в спец. форме;
        4. Пользователь должен нажать на специальную галочку, которая подтвердит всю серьёзность его намерений.

        Только после выполнения этих условий происходит удаление аккаунта. """

    # Инициализация формы для удаления аккаунта:
    form = DeleteProfileForm()

    # Проверяем, авторизован ли пользователь:
    if current_user.is_authenticated:

        # Если пользователь подтверждает удаление, то проверяем условия, после чего удаляем его профиль:
        if form.validate_on_submit():
            user = db_sess.query(User).filter(User.id == current_user.id).first()

            email = form.email.data
            password = form.password.data
            repeat_password = form.repeat_password.data
            confirm = form.confirm.data

            # 1. Пользователь должен ввести свою электронную почту, указанную у него в профиле:
            if current_user.email != email:
                return render_template(f'/user_pages/delete_profile{dt_prefix()}.html', form=form,
                                       message='Неправильно введена электронная почта')

            # 2. Пользователь должен указать свой текущий пароль:
            if not user.check_password(password):
                return render_template(f'/user_pages/delete_profile{dt_prefix()}.html', form=form,
                                       message='Вы указали неправильный пароль')

            # 3. Пользователь должен повторить свой текущий пароль в спец. форме:
            if password != repeat_password:
                return render_template(f'/user_pages/delete_profile{dt_prefix()}.html', form=form,
                                       message='Пароли не совпадают')

            # 4. Пользователь должен нажать на специальную галочку, которая подтвердит всю серьёзность его намерений:
            if not confirm:
                return render_template(f'user_pages/delete_profile{dt_prefix()}.html', form=form,
                                       message='Вы не нажали на галочку')

            # Если пройдены все условия, то удаляем аккаунт:

            # Прежде всего, удаляем библиотеку пользователя из БД:
            recognized_by_user = db_sess.query(Recognized).filter(Recognized.user_id == user.id).all()
            for r in recognized_by_user:
                db_sess.delete(r)

            # Удаляем пользователя, подтверждаем изменения, переводим пользователя на страницу авторизации:
            db_sess.delete(user)
            db_sess.commit()
            return redirect('/login')

        # Загружаем форму:
        return render_template(f'/user_pages/delete_profile{dt_prefix()}.html', form=form)

    # Ничего не загружаем, если пользователь не авторизован:
    return render_template(f'/user_pages/delete_profile{dt_prefix()}.html')


@app.route('/user/<int:user_id>')
def user_information(user_id):
    """ Данная страница отображает краткую информацию о зарегистрированном пользователе,
        а именно: его имя и фамилию, статистику и дату регистрации на платформе.
        Этой страницей также можно поделиться. """

    # Находим пользователя в БД:
    user = db_sess.query(User).filter(User.id == user_id).first()

    # Если пользователь найден, и при этом он не является администратором, то загружаем информацию:
    if user and user.id > 1:

        # Загрузка ссылки:
        o = urlparse(request.base_url)
        link = f'{o.netloc}/user/{user_id}'

        # Загрузка статистики:
        recognized_total = len(user.unique.split('&')) - 1
        user_lib = db_sess.query(Recognized).filter(Recognized.user_id == user.id).all()
        in_library = len(user_lib)
        in_featured = len([1 for u in user_lib if u.is_favourite == 1])

        # Загрузка страницы со всей информацией:
        return render_template(f'/information_pages/about_user{dt_prefix()}.html', user=user,
                               in_library=in_library, in_featured=in_featured,
                               recognized_total=recognized_total, link=link)

    # Загрузка пустой страницы:
    return render_template(f'/information_pages/about_user{dt_prefix()}.html')


@app.route('/administrator')
def administrator():
    """ Данная страница является кабинетом администратора.
        Администратор - это уникальный пользователь, владеющий первым идентефикатором в БД, своего рода владелец сайта,
        который имеет доступ к управлению всеми пользователями, зарегистрировавшимися на платформе.

        Эта страница включает в себя следующие функции для администратора:
            1. Просмотр информации о пользователе;
            2. Очистка оформления пользователя: установка стандартного изображения профиля,
               а также изменение имени и фамилии пользователя на нейтральные типа "Пользователь: Номер".
               Это создано в целях предупреждения пользователя о нарушении им основных правил сайта. Также
               Эта функция добавляет пользователю предупреждение о нарушении им правил.
               Если пользователь наберёт более 3 нарушений, то администратор имеет полное право
               удалить его аккаунт без возможности восстановления.
            3. Снять предупреждение;
            4. Удалить аккаунт - при соблюдении условия, прописанного в пункте 2. """

    # Проверяем, является ли пользователь администратором:
    is_admin()

    # Если проверка пройдена, то загружаем кабинет администратора:
    users = [u for u in db_sess.query(User).all() if u.id > 0]
    return render_template(f'/admin_page/admin{dt_prefix()}.html', users=users)


@app.route('/administrator/reset_user/<int:user_id>')
def admin_reset_user(user_id):
    """ Данная функция позволяет очистить оформление пользователя, а также выдать ему предупреждение.
        (подробнее: в комментариях к функции administrator()).
        Доступна только администратору сайта. """

    # Проверяем, является ли пользователь администратором:
    is_admin()

    # Если проверка пройдена, то производим необходимые операции:
    user = db_sess.query(User).filter(User.id == user_id).first()

    # Если пользователь существует в БД, то увеличиваем количество его предупреждений на 1, а также
    # очищаем его оформление:
    if user:
        user.warns += 1
        user.name = 'Пользователь'
        user.surname = f"{user.id}"

        if user.gender == 'Мужской':
            user.background = url_for('static', filename=MAN_PROFILE_PICTURE)
        else:
            user.background = url_for('static', filename=WOMAN_PROFILE_PICTURE)

        # Сохраняем изменения, направляем администратора обратно в кабинет:
        db_sess.commit()
    return redirect('/administrator')


@app.route('/administrator/undo_warn/<int:user_id>')
def admin_undo_warn(user_id):
    """ Данная функция позволяет снять предупреждение с пользователя
        (подробнее: в комментариях к функции administrator()).
        Доступна только администратору сайта. """

    # Проверяем, является ли пользователь администратором:
    is_admin()

    # Если пользователь существует в БД, то снимаем с него одно предупреждение:
    user = db_sess.query(User).filter(User.id == user_id).first()

    if user:
        if user.warns > 0:
            user.warns -= 1

        # Сохраняем изменения, направляем администратора обратно в кабинет:
        db_sess.commit()
    return redirect('/administrator')


@app.route('/administrator/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    """ Данная функция позволяет удалить аккаунт пользователя.
        (подробнее: в комментариях к функции administrator()).
        Доступна только администратору сайта. """

    # Проверяем, является ли пользователь администратором:
    is_admin()

    # Если пользователь существует в БД, то проверяем, есть ли у него от 3 предупреждений и выше;
    # если условие соблюдено, то удаляем аккаунт:
    user = db_sess.query(User).filter(User.id == user_id).first()

    if user:
        if user.warns >= 3:

            # Удаляем библиотку пользователя из БД:
            recognized_by_user = db_sess.query(Recognized).filter(Recognized.user_id == user.id).all()
            for rec in recognized_by_user:
                db_sess.delete(rec)

            # Удаляем пользователя, возвращаем администратора в кабинет:
            db_sess.delete(user)
            db_sess.commit()
    return redirect('/administrator')


if __name__ == '__main__':
    # Загружаем сессию БД:
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()

    # Специальное условие библиотеки Asyncio для OC Windows:
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

    # Запускаем приложение:
    app.run(debug=True)
