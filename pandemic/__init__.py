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
def mynavbar():
    return Navbar('pandemic',
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
    db.create_all()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')
