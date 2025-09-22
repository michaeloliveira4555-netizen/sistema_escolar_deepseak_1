# backend/services/dashboard_service.py

from datetime import date
from sqlalchemy import select, func
from ..models.database import db
from ..models.user import User
from ..models.aluno import Aluno
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from ..models.user_school import UserSchool
from ..models.horario import Horario
from ..models.semana import Semana
from ..models.turma import Turma
from sqlalchemy.orm import joinedload

class DashboardService:
    @staticmethod
    def get_dashboard_data(school_id=None):
        """
        Busca os dados estatísticos principais para o dashboard.
        """
        query_filters = [UserSchool.school_id == school_id] if school_id else []

        # Contagem total de usuários
        total_users_query = select(func.count(User.id)).join(UserSchool)
        if query_filters:
            total_users_query = total_users_query.where(*query_filters)
        total_users = db.session.scalar(total_users_query)

        # Contagem de alunos
        total_alunos_query = select(func.count(Aluno.id)).join(User, Aluno.user_id == User.id).join(UserSchool)
        if query_filters:
            total_alunos_query = total_alunos_query.where(*query_filters)
        total_alunos = db.session.scalar(total_alunos_query)

        # Contagem de instrutores
        total_instrutores_query = select(func.count(Instrutor.id)).join(User, Instrutor.user_id == User.id).join(UserSchool)
        if query_filters:
            total_instrutores_query = total_instrutores_query.where(*query_filters)
        total_instrutores = db.session.scalar(total_instrutores_query)
        
        # Contagem de disciplinas
        disciplinas_query = select(func.count(Disciplina.id))
        if school_id:
            disciplinas_query = disciplinas_query.where(Disciplina.school_id == school_id)
        total_disciplinas = db.session.scalar(disciplinas_query)

        # --- NOVOS DADOS PARA O DASHBOARD ---
        
        # Contagem de aulas pendentes de aprovação
        pendentes_query = select(func.count(Horario.id)).where(Horario.status == 'pendente')
        # Se um admin de escola estiver logado, filtramos pelas turmas daquela escola
        if school_id:
            turmas_da_escola = select(Turma.nome).where(Turma.school_id == school_id)
            pendentes_query = pendentes_query.where(Horario.pelotao.in_(turmas_da_escola))
        aulas_pendentes = db.session.scalar(pendentes_query)

        # Busca as próximas 5 aulas agendadas
        today = date.today()
        proximas_aulas_query = (
            select(Horario)
            .join(Semana)
            .where(Semana.data_fim >= today, Horario.status == 'confirmado')
            .options(
                joinedload(Horario.disciplina),
                joinedload(Horario.instrutor).joinedload(Instrutor.user),
                joinedload(Horario.semana)
            )
            .order_by(Semana.data_inicio, Horario.periodo)
            .limit(5)
        )
        if school_id:
            turmas_da_escola = select(Turma.nome).where(Turma.school_id == school_id)
            proximas_aulas_query = proximas_aulas_query.where(Horario.pelotao.in_(turmas_da_escola))
            
        proximas_aulas = db.session.scalars(proximas_aulas_query).all()

        return {
            'total_users': total_users,
            'total_alunos': total_alunos,
            'total_instrutores': total_instrutores,
            'total_disciplinas': total_disciplinas,
            'aulas_pendentes': aulas_pendentes,
            'proximas_aulas': proximas_aulas,
        }