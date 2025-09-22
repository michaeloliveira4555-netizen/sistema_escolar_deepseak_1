# tests/test_controllers.py

import pytest
from backend.models.user import User
from backend.models.database import db

class TestAuthController:
    """
    Suíte de testes de integração para o AuthController (endpoints de autenticação).
    """

    def test_login_redirects_to_complete_profile_for_new_student(self, test_client, test_app):
        """
        Testa que um novo aluno sem perfil é redirecionado para completar o cadastro.
        """
        with test_app.app_context():
            # 1. Setup: Cria um usuário aluno ATIVO mas SEM perfil de aluno
            password = "Password123!"
            user = User(
                id_func='112233',
                username='testuser',
                role='aluno',
                is_active=True,
                nome_completo="Novo Aluno"
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # 2. Ação: Simula o envio do formulário de login via POST (DENTRO DO CONTEXTO)
            response = test_client.post('/auth/login', data={
                'username': '112233',
                'password': password
            }, follow_redirects=False)

            # 3. Asserções (Verificações)
            assert response.status_code == 302
            assert response.location == '/aluno/completar-cadastro'

    def test_login_failure_wrong_password(self, test_client, test_app):
        """
        Testa uma tentativa de login com a senha incorreta.
        """
        with test_app.app_context():
            # 1. Setup
            user = User(
                id_func='445566',
                username='anotheruser',
                role='aluno',
                is_active=True
            )
            user.set_password('CorrectPassword!')
            db.session.add(user)
            db.session.commit()

            # 2. Ação: Envia uma requisição com a senha errada (DENTRO DO CONTEXTO)
            response = test_client.post('/auth/login', data={
                'username': '445566',
                'password': 'WrongPassword!'
            })

            # 3. Asserções
            assert response.status_code == 200
            assert b'Id Func/Usu\xc3\xa1rio ou senha inv\xc3\xa1lidos.' in response.data