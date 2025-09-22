# tests/test_services.py

import pytest
from datetime import date, timedelta
from backend.models.user import User
from backend.models.aluno import Aluno
from backend.models.instrutor import Instrutor
from backend.models.disciplina import Disciplina
from backend.models.turma import Turma
from backend.models.semana import Semana
from backend.models.horario import Horario
from backend.models.school import School
from backend.services.aluno_service import AlunoService
from backend.services.dashboard_service import DashboardService
from backend.models.database import db

def test_save_aluno_profile(test_app):
    """
    Testa a criação de um perfil de aluno através do AlunoService.
    """
    with test_app.app_context():
        # Setup
        school = School(nome="Escola de Teste")
        db.session.add(school)
        db.session.commit()
        
        user = User(id_func='987654', role='aluno', is_active=False, nome_completo="Aluno Teste")
        db.session.add(user)
        db.session.commit()

        aluno_data = {
            'matricula': '987654', 'opm': 'CRPO/VRP', 'turma_id': None, 'funcao_atual': 'Estudante'
        }

        # Ação
        success, message = AlunoService.save_aluno(user.id, aluno_data)

        # Asserções
        assert success is True
        assert "Perfil de aluno cadastrado" in message

        aluno_criado = db.session.query(Aluno).filter_by(user_id=user.id).one_or_none()
        assert aluno_criado is not None
        assert aluno_criado.opm == 'CRPO/VRP'

def test_get_dashboard_data_counts_pending_classes(test_app):
    """
    Testa se o DashboardService conta corretamente as aulas pendentes.
    """
    with test_app.app_context():
        # 1. Setup: Criar a estrutura necessária
        school = School(nome="Escola Dashboard")
        db.session.add(school)
        db.session.commit()

        turma = Turma(nome="1º Pelotão Teste", ano=2025, school_id=school.id)
        disciplina = Disciplina(materia="Teste de Software", carga_horaria_prevista=10, school_id=school.id)
        user_instrutor = User(id_func="instrutor123", role="instrutor", is_active=True, nome_de_guerra="Sgt Teste")
        db.session.add(user_instrutor)
        db.session.commit() # Commit para gerar o user_instrutor.id

        # CORREÇÃO APLICADA AQUI: Passando user_id em vez de user
        instrutor = Instrutor(user_id=user_instrutor.id, matricula="instrutor123", especializacao="Testes", formacao="Engenharia")
        semana = Semana(nome="Semana de Testes", data_inicio=date.today(), data_fim=date.today() + timedelta(days=4))
        db.session.add_all([turma, disciplina, instrutor, semana])
        db.session.commit()

        # Criar 2 aulas pendentes e 1 confirmada
        aula_pendente1 = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="segunda", periodo=1, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="pendente")
        aula_pendente2 = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="terca", periodo=2, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="pendente")
        aula_confirmada = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="quarta", periodo=3, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="confirmado")
        db.session.add_all([aula_pendente1, aula_pendente2, aula_confirmada])
        db.session.commit()

        # 2. Ação: Chamar o serviço
        dashboard_data = DashboardService.get_dashboard_data(school_id=school.id)

        # 3. Asserção: Verificar a contagem
        assert dashboard_data['aulas_pendentes'] == 2