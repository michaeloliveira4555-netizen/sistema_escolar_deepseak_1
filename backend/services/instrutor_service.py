from ..models.database import db
from ..models.instrutor import Instrutor
from ..models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app

class InstrutorService:
    @staticmethod
    def create_instrutor_with_user(form):
        try:
            user_exists_id_func = db.session.execute(db.select(User).filter_by(id_func=form.matricula.data)).scalar_one_or_none()
            if user_exists_id_func:
                return False, 'Esta matrícula (Id Funcional) já está em uso.'

            new_user = User(
                id_func=form.matricula.data,
                username=form.matricula.data,
                nome_completo=form.nome_completo.data,
                email=form.email.data,
                role='instrutor',
                is_active=True
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()

            success, message = InstrutorService.save_instrutor(new_user.id, form)

            if not success:
                db.session.delete(new_user)
                db.session.commit()
                return False, message

            return True, "Instrutor cadastrado com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar instrutor: {e}")
            return False, f"Erro ao cadastrar instrutor: {str(e)}"

    @staticmethod
    def save_instrutor(user_id, form):
        existing_instrutor = db.session.execute(
            select(Instrutor).where(Instrutor.user_id == user_id)
        ).scalar_one_or_none()
        if existing_instrutor:
            return False, "Este usuário já possui um perfil de instrutor cadastrado."

        try:
            novo_instrutor = Instrutor(
                user_id=user_id,
                matricula=form.matricula.data,
                especializacao=form.especializacao.data,
                formacao=form.formacao.data,
                telefone=form.telefone.data
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
    def update_instrutor(instrutor_id: int, form):
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return False, "Instrutor não encontrado."

        try:
            instrutor.user.nome_completo = form.nome_completo.data
            instrutor.user.email = form.email.data
            instrutor.matricula = form.matricula.data
            instrutor.especializacao = form.especializacao.data
            instrutor.formacao = form.formacao.data
            instrutor.telefone = form.telefone.data
            
            db.session.commit()
            return True, "Perfil do instrutor atualizado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade de dados. Verifique se a matrícula já existe."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar instrutor: {e}")
            return False, f"Erro inesperado ao atualizar instrutor: {str(e)}"