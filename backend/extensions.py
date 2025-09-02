# backend/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Apenas criamos as instâncias aqui, sem configurar com o 'app'
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()