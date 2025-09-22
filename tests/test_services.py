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
from backend.models.user_school import UserSchool
from backend.services.aluno_service import AlunoService
from backend.services.dashboard_service import DashboardService
from backend.models.database import db

def test_save_aluno_profile(test_app):
    """
    Testa a criação de um perfil de aluno através do AlunoService.
    """
    with test_app.app_context():
        school = School(nome="Escola de Teste")
        user = User(id_func='987654', role='aluno', is_active=False, nome_completo="Aluno Teste")
        db.session.add_all([school, user])
        db.session.commit()

        association = UserSchool(user_id=user.id, school_id=school.id, role='aluno')
        db.session.add(association)
        db.session.commit()

        aluno_data = {
            'matricula': '987654', 'opm': 'CRPO/VRP', 'turma_id': None, 'funcao_atual': 'Estudante'
        }
        success, message = AlunoService.save_aluno(user.id, aluno_data)

        assert success is True
        aluno_criado = db.session.query(Aluno).filter_by(user_id=user.id).one_or_none()
        assert aluno_criado is not None
        assert aluno_criado.opm == 'CRPO/VRP'

def test_get_dashboard_data_counts_pending_classes(test_app):
    """
    Testa se o DashboardService conta corretamente as aulas pendentes.
    """
    with test_app.app_context():
        # Setup
        school = School(nome="Escola Dashboard")
        db.session.add(school)
        db.session.commit()

        turma = Turma(nome="1º Pelotão Teste", ano=2025, school_id=school.id)
        disciplina = Disciplina(materia="Teste de Software", carga_horaria_prevista=10, school_id=school.id)
        user_instrutor = User(id_func="instrutor123", role="instrutor", is_active=True, nome_de_guerra="Sgt Teste")
        db.session.add(user_instrutor)
        db.session.commit()

        instrutor = Instrutor(user_id=user_instrutor.id, matricula="instrutor123", especializacao="Testes", formacao="Engenharia")
        semana = Semana(nome="Semana de Testes", data_inicio=date.today(), data_fim=date.today() + timedelta(days=4))
        db.session.add_all([turma, disciplina, instrutor, semana])
        db.session.commit()

        # Aulas
        aula_pendente1 = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="segunda", periodo=1, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="pendente")
        aula_pendente2 = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="terca", periodo=2, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="pendente")
        aula_confirmada = Horario(pelotao=turma.nome, semana_id=semana.id, dia_semana="quarta", periodo=3, disciplina_id=disciplina.id, instrutor_id=instrutor.id, status="confirmado")
        db.session.add_all([aula_pendente1, aula_pendente2, aula_confirmada])
        db.session.commit()

        # Ação
        dashboard_data = DashboardService.get_dashboard_data(school_id=school.id)

        # Asserção
        assert dashboard_data['aulas_pendentes'] == 2

def test_dashboard_fetches_recent_activity(test_app):
    """
    Testa se o DashboardService busca corretamente os usuários mais recentes.
    """
    with test_app.app_context():
        # 1. Setup: Cria uma escola e 6 usuários associados a ela
        school = School(nome="Escola Atividade Recente")
        db.session.add(school)
        db.session.commit()

        nomes = ["Usuario Antigo", "Usuario 2", "Usuario 3", "Usuario 4", "Usuario 5", "Usuario Mais Recente"]
        for i, nome in enumerate(nomes):
            user = User(id_func=f"user{i}", nome_completo=nome, is_active=True)
            db.session.add(user)
            db.session.commit()
            association = UserSchool(user_id=user.id, school_id=school.id, role='aluno')
            db.session.add(association)
            db.session.commit()

        # 2. Ação: Chama o serviço para buscar os dados do dashboard
        dashboard_data = DashboardService.get_dashboard_data(school_id=school.id)

        # 3. Asserções
        assert 'usuarios_recentes' in dashboard_data
        # Verifica se o serviço retornou o limite correto de 5 usuários
        assert len(dashboard_data['usuarios_recentes']) == 5
        # Verifica se o primeiro da lista é de fato o último que foi criado
        assert dashboard_data['usuarios_recentes'][0].nome_completo == "Usuario Mais Recente"
        # Verifica se o "Usuario Antigo" não está na lista, pois excedeu o limite de 5
        nomes_recentes = [u.nome_completo for u in dashboard_data['usuarios_recentes']]
        assert "Usuario Antigo" not in nomes_recentes