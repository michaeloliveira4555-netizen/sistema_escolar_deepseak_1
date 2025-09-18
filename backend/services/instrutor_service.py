from ..models.database import db
from ..models.instrutor import Instrutor
from ..models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from utils.validators import validate_telefone

class InstrutorService:
    def save_instrutor(user_id, data):
        existing_instrutor = db.session.execute(
            select(Instrutor).where(Instrutor.user_id == user_id)
        ).scalar_one_or_none()
        if existing_instrutor:
            return False, "Este usuário já possui um perfil de instrutor cadastrado."

        matricula_raw = data.get('matricula')
        if not matricula_raw:
            user = db.session.get(User, user_id)
            if not user:
                return False, "Usuário não encontrado."
            matricula_raw = user.id_func

        telefone_raw = data.get('telefone')
        especializacao = data.get('especializacao', '')
        formacao = data.get('formacao', '')
        is_rr_str = data.get('is_rr')

        if not telefone_raw:
            return False, "Telefone é um campo obrigatório."

        # Lógica para Posto/Graduação
        posto_graduacao_select = data.get('posto_graduacao_select')
        if posto_graduacao_select == 'Outro':
            posto_graduacao = data.get('posto_graduacao_outro', '')
        else:
            posto_graduacao = posto_graduacao_select

        matricula = ''.join(filter(str.isdigit, str(matricula_raw))) if matricula_raw else None
        telefone = ''.join(filter(str.isdigit, str(telefone_raw))) if telefone_raw else None

        if not matricula:
            return False, "Matrícula é um campo obrigatório."

        if not validate_telefone(telefone):
            return False, "Telefone inválido."
            
        is_rr = True if is_rr_str == 'sim' else False

        novo_instrutor = Instrutor(
            user_id=user_id,
            matricula=matricula,
            especializacao=especializacao,
            formacao=formacao,
            telefone=telefone
        )
        db.session.add(novo_instrutor)
        return True, "Perfil de instrutor cadastrado com sucesso!"

    @staticmethod
    def get_all_instrutores():
        stmt = select(Instrutor).join(User)
        stmt = stmt.where(User.role != 'super_admin')
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
        if not matricula_raw:
            user = instrutor.user
            if not user:
                return False, "Usuário associado não encontrado."
            matricula_raw = user.id_func

        telefone_raw = data.get('telefone')
        especializacao = data.get('especializacao', '')
        formacao = data.get('formacao', '')
        posto_graduacao = data.get('posto_graduacao')
        is_rr_str = data.get('is_rr')

        if not telefone_raw:
            return False, "Telefone é um campo obrigatório."

        matricula = ''.join(filter(str.isdigit, str(matricula_raw))) if matricula_raw else None
        telefone = ''.join(filter(str.isdigit, str(telefone_raw))) if telefone_raw else None

        if not matricula:
            return False, "Matrícula é um campo obrigatório."

        if not matricula.isdigit():
            return False, "Matrícula deve conter apenas números."
        if not validate_telefone(telefone):
            return False, "Telefone inválido."

        instrutor.matricula = matricula
        instrutor.especializacao = especializacao
        instrutor.formacao = formacao
        instrutor.telefone = telefone
            
        return True, "Perfil do instrutor atualizado com sucesso!"

    @staticmethod
    def delete_instrutor(instrutor_id: int):
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return False, "Instrutor não encontrado."

        try:
            user_a_deletar = instrutor.user
            db.session.delete(instrutor)
            db.session.delete(user_a_deletar)
            db.session.commit()
            return True, "Instrutor excluído com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir instrutor: {e}")
            return False, f"Erro ao excluir instrutor: {str(e)}"