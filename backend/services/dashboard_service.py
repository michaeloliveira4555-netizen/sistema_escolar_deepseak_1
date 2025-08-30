from ..models.database import db
from ..models.user import User
from ..models.aluno import Aluno
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina


class DashboardService:
    @staticmethod
    def get_dashboard_data():
        total_users = db.session.query(User).count()
        total_alunos = db.session.query(Aluno).count()
        total_instrutores = db.session.query(Instrutor).count()
        total_disciplinas = db.session.query(Disciplina).count()

        return {
            'total_users': total_users,
            'total_alunos': total_alunos,
            'total_instrutores': total_instrutores,
            'total_disciplinas': total_disciplinas,
        }