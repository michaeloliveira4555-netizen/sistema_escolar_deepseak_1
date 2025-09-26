# backend/services/user_service.py

from __future__ import annotations

from typing import Iterable, Optional, Tuple

from flask import current_app, session
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..models.database import db
from ..models.user import User
from ..models.user_school import UserSchool
from ..models.school import School


class UserService:
    @staticmethod
    def _normalize_school_id(raw_school_id: object) -> Optional[int]:
        """Converte o valor recebido do formulario em inteiro."""
        if raw_school_id in (None, "", "None"):
            return None
        try:
            return int(raw_school_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _attach_user_to_school(user: User, school: School, role: str) -> Tuple[bool, str, bool]:
        """Cria ou atualiza o vinculo UserSchool sem efetuar commit."""
        if not user or not school:
            return False, "Usuario ou escola nao encontrados.", False
        if not role:
            return False, "O papel de acesso e obrigatorio.", False

        existing_assignment = next(
            (assignment for assignment in user.user_schools if assignment.school_id == school.id),
            None,
        )

        created = False
        if existing_assignment:
            if existing_assignment.role != role:
                existing_assignment.role = role
                message = f"Papel atualizado para '{role}' na escola {school.nome}."
            else:
                message = f"O usuario ja estava vinculado como '{role}' na escola {school.nome}."
        else:
            db.session.add(UserSchool(user=user, school=school, role=role))
            created = True
            message = f"Usuario vinculado como '{role}' a escola {school.nome}."

        if user.role not in ["super_admin", "programador"]:
            user.role = role

        return True, message, created

    @staticmethod
    def pre_register_user(data: dict):
        id_func = (data.get("id_func") or "").strip()
        role = (data.get("role") or "").strip()
        school_id = UserService._normalize_school_id(data.get("school_id"))

        if not id_func or not role:
            return False, "ID funcional e papel sao obrigatorios."

        if school_id is None:
            return False, "Selecione a escola para concluir o pre-cadastro."

        school = db.session.get(School, school_id)
        if not school:
            return False, "Escola informada nao foi encontrada."

        existing_user = db.session.execute(
            select(User).filter_by(id_func=id_func)
        ).scalar_one_or_none()

        created_user = False
        if existing_user:
            user = existing_user
        else:
            user = User(id_func=id_func, role=role, is_active=False)
            db.session.add(user)
            created_user = True

        success, helper_message, _ = UserService._attach_user_to_school(user, school, role)
        if not success:
            db.session.rollback()
            return False, helper_message

        try:
            db.session.commit()
            if created_user:
                prefix = f"Usuario {id_func} pre-cadastrado com sucesso."
            else:
                prefix = f"Usuario {id_func} ja existia; vinculo atualizado."
            return True, f"{prefix} {helper_message}"
        except IntegrityError as exc:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade no pre-cadastro: {exc}")
            return False, "Erro de integridade ao salvar o pre-cadastro."
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado no pre-cadastro: {exc}")
            return False, "Erro inesperado ao salvar o pre-cadastro."

    @staticmethod
    def batch_pre_register_users(id_funcs: Iterable[str], role: str, school_id: Optional[int] = None):
        """Realiza pre-cadastro em lote e vincula todos a mesma escola."""
        normalized_role = (role or "").strip()
        if not normalized_role:
            return False, 0, 0

        normalized_school_id = UserService._normalize_school_id(school_id)
        if normalized_school_id is None:
            return False, 0, 0

        school = db.session.get(School, normalized_school_id)
        if not school:
            return False, 0, 0

        novos_usuarios_count = 0
        usuarios_existentes_count = 0

        for raw_id in id_funcs:
            id_func = (raw_id or "").strip()
            if not id_func:
                continue

            existing_user = db.session.execute(
                select(User).filter_by(id_func=id_func)
            ).scalar_one_or_none()

            if existing_user:
                user = existing_user
                usuarios_existentes_count += 1
            else:
                user = User(id_func=id_func, role=normalized_role, is_active=False)
                db.session.add(user)
                novos_usuarios_count += 1

            success, helper_message, _ = UserService._attach_user_to_school(user, school, normalized_role)
            if not success:
                db.session.rollback()
                current_app.logger.error(f"Falha ao vincular {id_func}: {helper_message}")
                return False, 0, 0

        try:
            db.session.commit()
            return True, novos_usuarios_count, usuarios_existentes_count
        except IntegrityError as exc:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade no pre-cadastro em lote: {exc}")
            return False, 0, 0
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado no pre-cadastro em lote: {exc}")
            return False, 0, 0

    @staticmethod
    def assign_school_role(user_id, school_id, role):
        if not all([user_id, school_id, role]):
            return False, "Usuario, escola e papel sao obrigatorios."

        user = db.session.get(User, user_id)
        school = db.session.get(School, school_id)

        success, message, _ = UserService._attach_user_to_school(user, school, role)
        if not success:
            return False, message

        try:
            db.session.commit()
            return True, message
        except IntegrityError as exc:
            db.session.rollback()
            current_app.logger.error(
                f"Erro de integridade ao vincular usuario {user_id} a escola {school_id}: {exc}"
            )
            return False, "Ocorreu um erro de integridade; verifique se o vinculo ja existe."
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao vincular usuario {user_id}: {exc}")
            return False, "Erro inesperado ao vincular o usuario."

    @staticmethod
    def remove_school_role(user_id, school_id):
        if not user_id or not school_id:
            return False, "Usuario e escola sao obrigatorios."

        assignment = db.session.execute(
            select(UserSchool).filter_by(user_id=user_id, school_id=school_id)
        ).scalar_one_or_none()

        if not assignment:
            return False, "Vinculo nao encontrado para este usuario e escola."

        user = assignment.user
        remaining_assignments = [us for us in user.user_schools if us.id != assignment.id]

        db.session.delete(assignment)

        if user and user.role not in ["super_admin", "programador"]:
            if remaining_assignments:
                user.role = remaining_assignments[0].role
            else:
                user.role = "aluno"

        try:
            db.session.commit()
            return True, "Vinculo removido com sucesso."
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(
                f"Erro ao remover vinculo do usuario {user_id} com a escola {school_id}: {exc}"
            )
            return False, "Erro inesperado ao remover o vinculo."

    @staticmethod
    def get_current_school_id():
        """Retorna o id da escola em contexto para o usuario autenticado."""
        if current_user.is_authenticated:
            if current_user.role in ['super_admin', 'programador']:
                return session.get('view_as_school_id')

            user_school = db.session.execute(
                select(UserSchool).filter_by(user_id=current_user.id)
            ).scalar_one_or_none()

            if user_school:
                return user_school.school_id

        return None

    @staticmethod
    def delete_user_by_id(user_id: int):
        """Exclui permanentemente um usuario e seus dados associados."""
        user = db.session.get(User, user_id)
        if not user:
            return False, "Usuario nao encontrado."

        if user.role in ['super_admin', 'programador']:
            return False, "Nao e permitido excluir um Super Admin ou Programador."

        try:
            db.session.delete(user)
            db.session.commit()
            return True, f"Usuario '{user.nome_completo or user.id_func}' foi excluido permanentemente."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir usuario: {e}")
            return False, "Ocorreu um erro interno ao tentar excluir o usuario."
