from ..extensions import db
from ..models.disciplina import Disciplina
from ..models.user import User  # IMPORTAÇÃO ADICIONADA AQUI
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
    @staticmethod
    def save_disciplina(data):
        nome_materia = data.get('materia')
        carga_horaria = data.get('carga_horaria_prevista')
        instrutor_id = data.get('instrutor_id')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
            instrutor_id_int = int(instrutor_id) if instrutor_id and instrutor_id.isdigit() else None
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
                carga_horaria_prevista=carga_horaria_int,
                instrutor_id=instrutor_id_int
            )
            db.session.add(nova_disciplina)
            db.session.commit()
            return True, "Disciplina cadastrada com sucesso!"
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
        instrutor_id = data.get('instrutor_id')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
            instrutor_id_int = int(instrutor_id) if instrutor_id and instrutor_id.isdigit() else None
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        try:
            disciplina.materia = nome_materia
            disciplina.carga_horaria_prevista = carga_horaria_int
            disciplina.instrutor_id = instrutor_id_int
            
            db.session.commit()
            return True, "Disciplina atualizada com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matéria já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar disciplina: {e}")
            return False, f"Erro inesperado ao atualizar disciplina: {str(e)}"

    @staticmethod
    def update_disciplina_instrutor(disciplina_id: int, instrutor_user_id: int):
        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, "Disciplina não encontrada."
        
        instrutor_profile = db.session.execute(
            select(User).where(User.id == instrutor_user_id)
        ).scalar_one_or_none()
        
        if instrutor_profile and instrutor_profile.instrutor_profile:
            disciplina.instrutor_id = instrutor_profile.instrutor_profile.id
            db.session.commit()
            return True, "Instrutor vinculado à disciplina com sucesso!"
        return False, "Perfil de instrutor não encontrado para o usuário."

    @staticmethod
    def remove_instrutor_from_disciplina(instrutor_user_id: int):
        instrutor_profile = db.session.execute(
            select(User).where(User.id == instrutor_user_id)
        ).scalar_one_or_none()
        
        if instrutor_profile and instrutor_profile.instrutor_profile:
            instrutor_id = instrutor_profile.instrutor_profile.id
            disciplinas = db.session.execute(
                select(Disciplina).where(Disciplina.instrutor_id == instrutor_id)
            ).scalars().all()
            for disciplina in disciplinas:
                disciplina.instrutor_id = None
            db.session.commit()
            return True, "Instrutor desvinculado das disciplinas com sucesso!"
        return False, "Perfil de instrutor não encontrado para o usuário."