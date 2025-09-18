from ..models.database import db
from ..models.user import User
from ..models.aluno import Aluno
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from ..models.user_school import UserSchool

class DashboardService:
    @staticmethod
    def get_dashboard_data(school_id=None):
        if school_id:
            # Query for a specific school
            total_users = db.session.query(User).join(UserSchool).filter(UserSchool.school_id == school_id).count()
            total_alunos = db.session.query(Aluno).join(User, Aluno.user_id == User.id).join(UserSchool).filter(UserSchool.school_id == school_id).count()
            total_instrutores = db.session.query(Instrutor).join(User, Instrutor.user_id == User.id).join(UserSchool).filter(UserSchool.school_id == school_id).count()
            # A contagem de disciplinas por escola é mais complexa, pode estar ligada a Turmas.
            # Por enquanto, retornaremos 0 para evitar erros.
            total_disciplinas = 0 # Placeholder
        else:
            # Query global (como estava antes)
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