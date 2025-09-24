# tests/conftest.py

import pytest
from backend.app import create_app
from backend.models.database import db as _db
from backend.models.user import User
from backend.config import Config
from flask_login import login_user, logout_user

class TestingConfig(Config):
    """Configuração dedicada para o ambiente de testes."""
    TESTING = True
    SECRET_KEY = "uma-chave-secreta-para-testes"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    @staticmethod
    def init_app(app):
        pass

@pytest.fixture(scope='function')
def test_app():
    """Cria e configura uma instância da aplicação para cada teste."""
    app = create_app(config_class=TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def db_session(test_app):
    """Fornece a sessão do banco de dados da aplicação."""
    with test_app.app_context():
        yield _db.session

@pytest.fixture(scope='function')
def test_client(test_app):
    """Cria um cliente de teste para simular requisições HTTP."""
    return test_app.test_client()

@pytest.fixture(scope='function')
def new_user(db_session):
    """Fixture para criar um novo usuário padrão."""
    user = User(username='testuser', id_func='12345', email='test@example.com', role='aluno', is_active=True)
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope='function')
def logged_in_user(test_app, new_user):
    """Fixture para simular um usuário logado."""
    with test_app.test_request_context():
        login_user(new_user)
        yield new_user
        logout_user()

@pytest.fixture(scope='function')
def new_super_admin(db_session):
    """Fixture para criar um novo usuário super_admin."""
    admin = User(username='superadmin', id_func='54321', email='admin@example.com', role='super_admin', is_active=True)
    admin.set_password('adminpass')
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture(scope='function')
def logged_in_super_admin(test_app, new_super_admin):
    """Fixture para simular um super_admin logado."""
    with test_app.test_request_context():
        login_user(new_super_admin)
        yield new_super_admin
        logout_user()
