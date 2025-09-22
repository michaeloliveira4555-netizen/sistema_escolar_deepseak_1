# backend/services/instrutor_service.py

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
        """Cria um novo perfil de instrutor para um usuário existente."""
        if db.session.execute(select(Instrutor).where(Instrutor.user_id == user_id)).scalar_one_or_none():
            return False, "Este usuário já possui um perfil de instrutor."

        user = db.session.get(User, user_id)
        if not user:
            return False, "Usuário associado não encontrado."

        # Processa os dados do formulário
        posto_graduacao_select = data.get('posto_graduacao_select')
        posto_graduacao = data.get('posto_graduacao_outro', '') if posto_graduacao_select == 'Outro' else posto_graduacao_select
        
        is_rr = data.get('is_rr') == 'sim'
        telefone = data.get('telefone', '')

        if not validate_telefone(telefone):
            return False, "Formato de telefone inválido."

        try:
            novo_instrutor = Instrutor(
                user_id=user_id,
                matricula=user.id_func,
                especializacao=data.get('especializacao', ''),
                formacao=data.get('formacao', ''),
                telefone=telefone,
                posto_graduacao=posto_graduacao,
                credor=data.get('credor'),
                is_rr=is_rr
            )
            db.session.add(novo_instrutor)
            db.session.commit()
            return True, "Perfil de instrutor cadastrado com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar perfil de instrutor: {e}")
            return False, "Ocorreu um erro ao salvar o perfil."

    @staticmethod
    def get_all_instrutores():
        """Retorna todos os instrutores ordenados pelo nome."""
        return db.session.scalars(
            select(Instrutor).join(User).order_by(User.nome_completo)
        ).all()

    @staticmethod
    def get_instrutor_by_id(instrutor_id: int):
        return db.session.get(Instrutor, instrutor_id)

    @staticmethod
    def update_instrutor(instrutor_id: int, data: dict):
        """Atualiza o perfil de um instrutor existente."""
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return False, "Instrutor não encontrado."

        try:
            instrutor.especializacao = data.get('especializacao')
            instrutor.formacao = data.get('formacao')
            instrutor.telefone = data.get('telefone')
            instrutor.credor = data.get('credor')
            instrutor.is_rr = data.get('is_rr') == 'sim'
            
            db.session.commit()
            return True, "Perfil do instrutor atualizado com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao atualizar instrutor: {e}")
            return False, "Ocorreu um erro ao atualizar o perfil."

    @staticmethod
    def delete_instrutor(instrutor_id: int):
        """Exclui um instrutor e o usuário associado a ele."""
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return False, "Instrutor não encontrado."

        try:
            # A exclusão do usuário acionará a exclusão em cascata do perfil
            user_a_deletar = instrutor.user
            db.session.delete(user_a_deletar)
            db.session.commit()
            return True, "Instrutor e usuário associado foram excluídos com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir instrutor: {e}")
            return False, f"Erro ao excluir instrutor: {str(e)}"