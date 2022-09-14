import os
from os import environ as env
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
MIGRATIONS_DIR = os.path.abspath(os.path.dirname(__file__) + '/migrations')
migrate = Migrate(app, db, directory=MIGRATIONS_DIR)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models
