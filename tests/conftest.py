# tests/conftest.py

import pytest
from backend.app import create_app
from backend.models.database import db
from backend.config import Config

class TestingConfig(Config):
    """Configuração dedicada para o ambiente de testes."""
    TESTING = True
    SECRET_KEY = "uma-chave-secreta-para-testes"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    @staticmethod
    def init_app(app):
        # Sobrescreve o método para não fazer a verificação da SECRET_KEY em ambiente de teste
        pass

@pytest.fixture(scope='module')
def test_app():
    """Cria e configura uma instância da aplicação para a suíte de testes."""
    app = create_app(config_class=TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """Cria um cliente de teste para simular requisições HTTP."""
    return test_app.test_client()