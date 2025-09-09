from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.user import User
from ..models.turma import Turma
from ..models.disciplina_turma import DisciplinaTurma
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
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
            # 1. Cria a nova disciplina
            nova_disciplina = Disciplina(
                materia=nome_materia,
                carga_horaria_prevista=carga_horaria_int
            )
            db.session.add(nova_disciplina)
            db.session.commit()

            # 2. Busca todas as turmas existentes
            turmas = db.session.scalars(select(Turma)).all()
            
            # 3. Cria a associação da nova disciplina para cada turma
            for turma in turmas:
                associacao = DisciplinaTurma(
                    pelotao=turma.nome,
                    disciplina_id=nova_disciplina.id
                )
                db.session.add(associacao)
            
            db.session.commit()
            return True, "Disciplina cadastrada e associada a todas as turmas com sucesso!"
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
            
    # As funções abaixo foram mantidas para evitar quebras em outras partes do sistema
    @staticmethod
    def update_disciplina_instrutor(disciplina_id: int, user_id: int):
        current_app.logger.info(
            f"Tentativa de associar disciplina principal (ID: {disciplina_id}) "
            f"ao usuário (ID: {user_id}). Nenhuma ação foi tomada pois a associação é por pelotão."
        )
        return True, "Operação concluída. As associações de instrutores são gerenciadas por pelotão na tela de Disciplinas."

    @staticmethod
    def remove_instrutor_from_disciplina(user_id: int):
        user = db.session.get(User, user_id)
        if not user or not user.instrutor_profile:
            return False, "Instrutor não encontrado."
        
        instrutor_id = user.instrutor_profile.id
        
        try:
            db.session.query(DisciplinaTurma).filter(
                DisciplinaTurma.instrutor_id_2 == instrutor_id
            ).update({'instrutor_id_2': None})
            db.session.commit()
            return True, "Instrutor removido de todas as posições secundárias."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao remover instrutor de disciplina como secundário: {e}")
            return False, "Erro ao remover instrutor de posições secundárias."