# backend/config.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'escola.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BABEL_DEFAULT_LOCALE = 'pt_BR'

    @staticmethod
    def init_app(app):
        """
        Executa verificações de configuração depois que a app foi criada.
        Isso evita erros durante a importação em ambientes de teste.
        """
        if not app.config.get("SECRET_KEY") and not app.testing:
            raise ValueError("No SECRET_KEY set for Flask application. Set the SECRET_KEY environment variable.")