from flask_login import LoginManager
from flask import Flask

from data.ORM import db_session
from data.ORM import user

app = Flask(__name__)


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
    return 'Main Page'


if __name__ == '__main__':
    db_session.global_init("db/PyJam.db")
    db_sess = db_session.create_session()
    app.run()
