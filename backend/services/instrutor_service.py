from ..models.database import db
from ..models.instrutor import Instrutor
from ..models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from utils.validators import validate_telefone

class InstrutorService:
    @staticmethod
    def save_instrutor(user_id, data):
        existing_instrutor = db.session.execute(
            select(Instrutor).where(Instrutor.user_id == user_id)
        ).scalar_one_or_none()
        if existing_instrutor:
            return False, "Este usuário já possui um perfil de instrutor cadastrado."

        matricula_raw = data.get('matricula')
        telefone_raw = data.get('telefone')
        especializacao = data.get('especializacao', '') # Aceita campo vazio
        formacao = data.get('formacao', '') # Aceita campo vazio

        matricula = ''.join(filter(str.isdigit, matricula_raw)) if matricula_raw else None
        telefone = ''.join(filter(str.isdigit, telefone_raw)) if telefone_raw else None

        if not matricula:
            return False, "Matrícula é um campo obrigatório."
        
        if not matricula.isdigit():
            return False, "Matrícula deve conter apenas números."
        if telefone and not validate_telefone(telefone):
            return False, "Telefone inválido."

        try:
            novo_instrutor = Instrutor(
                user_id=user_id,
                matricula=matricula,
                especializacao=especializacao,
                formacao=formacao,
                telefone=telefone
            )
            db.session.add(novo_instrutor)
            db.session.commit()
            return True, "Perfil de instrutor cadastrado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade de dados. Verifique se a matrícula já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar instrutor: {e}")
            return False, f"Erro inesperado ao cadastrar instrutor: {str(e)}"

    @staticmethod
    def get_all_instrutores():
        stmt = select(Instrutor).join(User)
        stmt = stmt.where(User.role != 'admin')
        stmt = stmt.order_by(User.username)
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_instrutor_by_id(instrutor_id: int):
        return db.session.get(Instrutor, instrutor_id)

    @staticmethod
    def update_instrutor(instrutor_id: int, data: dict):
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return False, "Instrutor não encontrado."

        matricula_raw = data.get('matricula')
        telefone_raw = data.get('telefone')
        especializacao = data.get('especializacao', '') # Aceita campo vazio
        formacao = data.get('formacao', '') # Aceita campo vazio

        matricula = ''.join(filter(str.isdigit, matricula_raw)) if matricula_raw else None
        telefone = ''.join(filter(str.isdigit, telefone_raw)) if telefone_raw else None

        if not matricula:
            return False, "Matrícula é um campo obrigatório."
        
        if not matricula.isdigit():
            return False, "Matrícula deve conter apenas números."
        if telefone and not validate_telefone(telefone):
            return False, "Telefone inválido."

        try:
            instrutor.matricula = matricula
            instrutor.especializacao = especializacao
            instrutor.formacao = formacao
            instrutor.telefone = telefone
            
            db.session.commit()
            return True, "Perfil do instrutor atualizado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade de dados. Verifique se a matrícula já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar instrutor: {e}")
            return False, f"Erro inesperado ao atualizar instrutor: {str(e)}"