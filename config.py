import os
from os import environ as env


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = env.get('GCH_SECRET_KEY', '"#>Ad:t{E-e\"JY3o&dm[`')
    SQLALCHEMY_DATABASE_URI = env.get('GCH_DB_URL', 'sqlite:///' + os.path.join(basedir, 'db.sqlite3'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
