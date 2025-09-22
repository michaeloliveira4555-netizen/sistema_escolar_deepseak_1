# tests/test_controllers.py

import pytest
from backend.models.user import User
from backend.models.school import School
from backend.models.user_school import UserSchool
from backend.models.database import db
from flask import session

class TestAuthController:
    """
    Suíte de testes de integração para o AuthController (endpoints de autenticação).
    """
    def test_login_redirects_to_complete_profile_for_new_student(self, test_client, test_app):
        """Testa que um novo aluno sem perfil é redirecionado para completar o cadastro."""
        with test_app.app_context():
            password = "Password123!"
            user = User(id_func='112233', username='testuser', role='aluno', is_active=True, nome_completo="Novo Aluno")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            response = test_client.post('/auth/login', data={'username': '112233', 'password': password}, follow_redirects=False)

            assert response.status_code == 302
            assert response.location == '/aluno/completar-cadastro'

    def test_login_failure_wrong_password(self, test_client, test_app):
        """Testa uma tentativa de login com a senha incorreta."""
        with test_app.app_context():
            user = User(id_func='445566', username='anotheruser', role='aluno', is_active=True)
            user.set_password('CorrectPassword!')
            db.session.add(user)
            db.session.commit()

            response = test_client.post('/auth/login', data={'username': '445566', 'password': 'WrongPassword!'})

            assert response.status_code == 200
            assert b'Id Func/Usu\xc3\xa1rio ou senha inv\xc3\xa1lidos.' in response.data

class TestPermissionSystem:
    """
    Suíte de testes para o sistema de permissões e roles.
    """
    def test_school_admin_cannot_access_super_admin_dashboard(self, test_client, test_app):
        """Garante que um usuário com role 'admin_escola' não pode acessar o dashboard de super admin."""
        with test_app.app_context():
            school = School(nome="Escola Admin Teste")
            password = "PasswordAdmin123!"
            school_admin_user = User(id_func='admin01', role='admin_escola', is_active=True, nome_completo="Admin da Escola")
            school_admin_user.set_password(password)
            db.session.add_all([school, school_admin_user])
            db.session.commit()
            
            association = UserSchool(user_id=school_admin_user.id, school_id=school.id, role='admin_escola')
            db.session.add(association)
            db.session.commit()

            test_client.post('/auth/login', data={'username': 'admin01', 'password': password})
            response = test_client.get('/super-admin/dashboard', follow_redirects=True)

            assert response.status_code == 200
            assert b'Voc\xc3\xaa n\xc3\xa3o tem permiss\xc3\xa3o para acessar esta p\xc3\xa1gina.' in response.data

    def test_super_admin_view_as_school_context(self, test_client, test_app):
        """
        Testa se o super admin pode entrar e sair do modo de visualização de escola.
        """
        with test_app.app_context():
            # 1. Setup: Cria uma escola e um super admin
            school = School(nome="Escola de Teste SA")
            password = "SuperPassword123!"
            super_admin_user = User(id_func='superadmin', role='super_admin', is_active=True, nome_completo="Super Admin")
            super_admin_user.set_password(password)
            db.session.add_all([school, super_admin_user])
            db.session.commit()

            # 2. Ação: Login como super admin
            test_client.post('/auth/login', data={'username': 'superadmin', 'password': password})

            # 3. Ação: Entra no modo de visualização
            test_client.get(f'/dashboard?view_as_school={school.id}')

            # 4. Asserção: Verifica se a session foi populada corretamente
            # Usamos session_transaction para acessar a session fora de uma requisição
            with test_client.session_transaction() as sess:
                assert sess.get('view_as_school_id') == school.id
                assert sess.get('view_as_school_name') == "Escola de Teste SA"

            # 5. Ação: Sai do modo de visualização
            test_client.get('/super-admin/exit-view')

            # 6. Asserção: Verifica se a session foi limpa
            with test_client.session_transaction() as sess:
                assert 'view_as_school_id' not in sess
                assert 'view_as_school_name' not in sess