import sqlalchemy as sa  # Сначала импортируем необходимое — саму библиотеку sqlalchemy
import sqlalchemy.orm as orm  # Часть библиотеки, которая отвечает за функциональность ORM
from sqlalchemy.orm import Session  # Объект Session, отвечающий за соединение с базой данных
import sqlalchemy.ext.declarative as dec  # Модуль declarative — он поможет нам объявить нашу базу данных


# Абстрактная декларативная база, в которую позднее будем наследовать все наши модели
SqlAlchemyBase = dec.declarative_base()

# Используем для получения сессий подключения к нашей базе данных
__factory = None


def global_init(db_file):
    global __factory

    # Проверка: не создали ли мы уже фабрику подключений. Если уже создали, то завершаем работу,
    # так как начальную инициализацию надо проводить только единожды:
    if __factory:
        return

    # Проверяем, что нам указали непустой адрес базы данных
    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # создаем строку подключения conn_str
    # (она состоит из типа базы данных, адреса до базы данных и параметров подключения), которую
    # передаем Sqlalchemy для того, чтобы она выбрала правильный движок работы с базой данных
    # (переменная engine):
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    # Прим. Если в функцию create_engine() передать параметр echo со значением True, в консоль будут выводиться все
    # SQL-запросы, которые сделает SQLAlchemy, что очень удобно для отладки:
    engine = sa.create_engine(conn_str, echo=False)

    # Создаем фабрику подключений к нашей базе данных, которая будет работать с нужным нам движком
    __factory = orm.sessionmaker(bind=engine)

    # Импортируем все из файла __all_models.py — именно тут SQLalchemy узнает о всех наших моделях:
    # noinspection PyUnresolvedReferences
    from . import __all_models

    # Заставляем нашу базу данных создать все объекты, которые она пока не создала.
    # Обратите внимание: все таблицы, которые были уже созданы в базе данных, останутся без изменений:
    SqlAlchemyBase.metadata.create_all(engine)


# Функция create_session нужна для получения сессии подключения к нашей базе данных. Часть -> Session нужна лишь для
# того, чтобы явно указать PyCharm, что наша функция возвращает объект типа
# sqlalchemy.orm.Session и среда могла показывать нам подсказки далее:
def create_session() -> Session:
    global __factory
    return __factory()
