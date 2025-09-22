# tests/test_services.py

import pytest
from backend.models.user import User
from backend.models.aluno import Aluno
from backend.services.aluno_service import AlunoService
from backend.models.database import db

def test_save_aluno_profile(test_app):
    """
    Testa a criação de um perfil de aluno através do AlunoService.
    A fixture 'test_app' é injetada automaticamente pelo pytest a partir do conftest.py.
    """
    with test_app.app_context():
        # 1. Setup: Cria um usuário base para o teste
        user = User(id_func='987654', role='aluno', is_active=False, nome_completo="Aluno Teste")
        db.session.add(user)
        db.session.commit()

        # Dados do formulário para criar o perfil do aluno
        aluno_data = {
            'matricula': '987654',
            'opm': 'CRPO/VRP',
            'turma_id': None,
            'funcao_atual': 'Estudante'
        }

        # 2. Ação: Chama o serviço para salvar o perfil do aluno
        success, message = AlunoService.save_aluno(user.id, aluno_data)

        # 3. Asserções (Verificações)
        assert success is True
        # Mensagem ajustada para refletir a nova lógica
        assert "Perfil de aluno cadastrado" in message

        # Verifica se o aluno foi realmente salvo no banco de dados
        aluno_criado = db.session.query(Aluno).filter_by(user_id=user.id).one_or_none()
        assert aluno_criado is not None
        assert aluno_criado.opm == 'CRPO/VRP'
        assert aluno_criado.matricula == '987654'