import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from config import config

import constants

bootstrap = Bootstrap()
db = SQLAlchemy()
nav = Nav()

@nav.navigation()
def navbar():
    return Navbar('Pandemic!',
                  View('Begin', 'main.begin'),
                  View('Draw', 'main.draw'),
                  View('Infect', 'main.infect'),
                  View('History', 'main.history'))


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    nav.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app


app = create_app(os.getenv('FLASK_CONFIG') or 'default')


def init_db():
    import models
    db.create_all()
    db.session.add_all([models.City(name=city_name, color=city_color)
                        for city_name,city_color in constants.CITIES.items()])
    db.session.add_all([models.Character(name=name, first_name=first_name,
                                         middle_name=middle_name, icon=icon)
                        for name,(first_name,middle_name,icon) in constants.CHARACTERS.items()])
    db.session.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')
