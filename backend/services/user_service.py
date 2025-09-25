# backend/services/user_service.py

from flask import current_app, session
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os

from ..models.database import db
from ..models.user import User
from ..models.aluno import Aluno
from ..models.user_school import UserSchool
from ..models.school import School
from ..services.asset_service import AssetService

class UserService:
    
    @staticmethod
    def pre_register_user(data):
        id_func = data.get('id_func')
        role = data.get('role')

        if not id_func or not role:
            return False, "ID Funcional e Função são obrigatórios."

        if db.session.execute(select(User).filter_by(id_func=id_func)).scalar_one_or_none():
            return False, f"O usuário com ID Funcional '{id_func}' já existe."

        try:
            new_user = User(id_func=id_func, role=role, is_active=False)
            db.session.add(new_user)
            db.session.commit()
            return True, f"Usuário {id_func} pré-cadastrado com sucesso como {role}."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro no pré-cadastro: {e}")
            return False, "Erro ao pré-cadastrar usuário."

    @staticmethod
    def batch_pre_register_users(id_funcs, role):
        novos_usuarios_count = 0
        usuarios_existentes_count = 0
        
        for id_func in id_funcs:
            if db.session.execute(select(User).filter_by(id_func=id_func)).scalar_one_or_none():
                usuarios_existentes_count += 1
                continue
            
            try:
                new_user = User(id_func=id_func, role=role, is_active=False)
                db.session.add(new_user)
                novos_usuarios_count += 1
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro no pré-cadastro em lote para {id_func}: {e}")
                # Decide se quer parar ou continuar em caso de erro
                # return False, f"Erro ao pré-cadastrar {id_func}."

        try:
            db.session.commit()
            return True, novos_usuarios_count, usuarios_existentes_count
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro final no commit do pré-cadastro em lote: {e}")
            return False, 0, 0

    @staticmethod
    def assign_school_role(user_id, school_id, role):
        if not all([user_id, school_id, role]):
            return False, "ID do usuário, ID da escola e função são obrigatórios."

        user = db.session.get(User, user_id)
        school = db.session.get(School, school_id)

        if not user or not school:
            return False, "Usuário ou escola não encontrados."

        existing_assignment = db.session.execute(
            select(UserSchool).filter_by(user_id=user_id, school_id=school_id)
        ).scalar_one_or_none()

        if existing_assignment:
            existing_assignment.role = role
        else:
            new_assignment = UserSchool(user_id=user_id, school_id=school_id, role=role)
            db.session.add(new_assignment)
        
        try:
            db.session.commit()
            return True, f"Função de '{role}' atribuída com sucesso a {user.nome_completo or user.id_func} na escola {school.nome}."
        except IntegrityError:
            db.session.rollback()
            return False, "Ocorreu um erro de integridade. A atribuição pode já existir."

    @staticmethod
    def remove_school_role(user_id, school_id):
        if not user_id or not school_id:
            return False, "ID do usuário e ID da escola são obrigatórios."

        assignment = db.session.execute(
            select(UserSchool).filter_by(user_id=user_id, school_id=school_id)
        ).scalar_one_or_none()

        if not assignment:
            return False, "Vínculo não encontrado para este usuário e escola."

        db.session.delete(assignment)
        db.session.commit()
        return True, "Vínculo com a escola removido com sucesso."

    @staticmethod
    def get_current_school_id():
        """
        Obtém o ID da escola do contexto atual do usuário.
        Para Super Admins, verifica o modo de visualização na sessão.
        Para outros usuários, obtém da sua associação direta.
        """
        if current_user.is_authenticated:
            if current_user.role in ['super_admin', 'programador']:
                return session.get('view_as_school_id')
            
            # Pega a primeira escola associada para outros roles
            user_school = db.session.execute(
                select(UserSchool).filter_by(user_id=current_user.id)
            ).scalar_one_or_none()
            
            if user_school:
                return user_school.school_id
                
        return None
    
    @staticmethod
    def delete_user_by_id(user_id: int):
        """Exclui permanentemente um usuário e todos os seus dados associados."""
        user = db.session.get(User, user_id)
        if not user:
            return False, "Usuário não encontrado."
        
        if user.role in ['super_admin', 'programador']:
            return False, "Não é permitido excluir um Super Admin ou Programador."

        try:
            # A exclusão em cascata configurada nos modelos irá remover
            # os perfis de aluno/instrutor e os vínculos com escolas.
            db.session.delete(user)
            db.session.commit()
            return True, f"Usuário '{user.nome_completo or user.id_func}' foi excluído permanentemente."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir usuário: {e}")
            return False, "Ocorreu um erro interno ao tentar excluir o usuário."