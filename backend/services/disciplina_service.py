from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.user import User
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.historico_disciplina import HistoricoDisciplina
from ..models.instrutor import Instrutor
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
    @staticmethod
    def get_disciplinas_with_instrutores_for_pelotao(pelotao: str):
        """
        Busca todas as associações de disciplina para um pelotão específico,
        garantindo que os dados do instrutor e do usuário sejam pré-carregados.
        """
        query = (
            select(DisciplinaTurma)
            .options(
                joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.instrutor_2).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.disciplina)
            )
            .join(Disciplina)
            .filter(DisciplinaTurma.pelotao == pelotao)
            .order_by(Disciplina.materia)
        )
        return db.session.scalars(query).unique().all()
        
    @staticmethod
    def save_disciplina(data):
        nome_materia = data.get('materia')
        carga_horaria = data.get('carga_horaria_prevista')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        existing_disciplina = db.session.execute(
            select(Disciplina).where(Disciplina.materia == nome_materia)
        ).scalar_one_or_none()
        if existing_disciplina:
            return False, "Uma disciplina com este nome já existe."

        try:
            nova_disciplina = Disciplina(
                materia=nome_materia,
                carga_horaria_prevista=carga_horaria_int
            )
            db.session.add(nova_disciplina)
            db.session.commit()

            todos_os_alunos = db.session.scalars(select(Aluno)).all()
            for aluno in todos_os_alunos:
                nova_matricula = HistoricoDisciplina(aluno_id=aluno.id, disciplina_id=nova_disciplina.id)
                db.session.add(nova_matricula)
            
            turmas = db.session.scalars(select(Turma)).all()
            for turma in turmas:
                associacao = DisciplinaTurma(
                    pelotao=turma.nome,
                    disciplina_id=nova_disciplina.id
                )
                db.session.add(associacao)

            db.session.commit()
            return True, "Disciplina cadastrada e associada a todos os alunos e turmas!"
        except IntegrityError:
            db.session.rollback()
            return False, "Uma disciplina com este nome já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar disciplina: {e}")
            return False, f"Erro inesperado ao cadastrar disciplina: {str(e)}"

    @staticmethod
    def get_all_disciplinas():
        stmt = select(Disciplina).order_by(Disciplina.materia)
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_disciplina_by_id(disciplina_id: int):
        return db.session.get(Disciplina, disciplina_id)

    @staticmethod
    def update_disciplina(disciplina_id: int, data: dict):
        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, "Disciplina não encontrada."

        nome_materia = data.get('materia')
        carga_horaria = data.get('carga_horaria_prevista')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        try:
            disciplina.materia = nome_materia
            disciplina.carga_horaria_prevista = carga_horaria_int
            
            db.session.commit()
            return True, "Disciplina atualizada com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matéria já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar disciplina: {e}")
            return False, f"Erro inesperado ao atualizar disciplina: {str(e)}"