from flask import current_app
from utils.validators import validate_password_strength

class UserService:
    @staticmethod
    def pre_register_user(data):
        id_func = data.get('id_func', '').strip()
        role = data.get('role')

        if not id_func or not role:
            return False, 'Por favor, preencha todos os campos.'

        if not id_func.isdigit():
            return False, 'A Identidade Funcional deve conter apenas números.'

        if db.session.execute(select(User).filter_by(id_func=id_func)).scalar_one_or_none():
            return False, f'A Id Func "{id_func}" já está pré-cadastrada no sistema.'

        try:
            new_user = User(
                id_func=id_func,
                role=role,
                is_active=False
            )
            db.session.add(new_user)
            db.session.commit()
            return True, f'Usuário com Id Func "{id_func}" pré-cadastrado com sucesso!'
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco de dados ao pré-cadastrar usuário: {e}")
            return False, f"Erro de banco de dados ao pré-cadastrar usuário: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao pré-cadastrar usuário: {e}")
            return False, f"Erro inesperado ao pré-cadastrar usuário: {str(e)}"

    @staticmethod
    def update_user_profile(user, data):
        nome_completo = data.get('nome_completo')
        email = data.get('email')
        telefone = data.get('telefone')
        credor = data.get('credor')

        senha_atual = data.get('senha_atual')
        nova_senha = data.get('nova_senha')
        confirmar_nova_senha = data.get('confirmar_nova_senha')

        user.nome_completo = nome_completo
        user.email = email

        if user.role == 'aluno' and user.aluno_profile:
            user.aluno_profile.telefone = telefone
        elif user.role == 'instrutor' and user.instrutor_profile:
            user.instrutor_profile.telefone = telefone
            user.instrutor_profile.credor = credor

        if senha_atual or nova_senha or confirmar_nova_senha:
            if not senha_atual:
                return False, 'Por favor, informe sua senha atual para alterar a senha.'
            if not user.check_password(senha_atual):
                return False, 'A senha atual está incorreta.'
            if not nova_senha or not confirmar_nova_senha:
                return False, 'Por favor, preencha os campos de nova senha e confirmação.'
            if nova_senha != confirmar_nova_senha:
                return False, 'A nova senha e a confirmação não coincidem.'
            
            is_strong, message = validate_password_strength(nova_senha)
            if not is_strong:
                return False, message

            user.set_password(nova_senha)

        try:
            db.session.commit()
            return True, 'Perfil atualizado com sucesso!'
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco de dados ao atualizar perfil: {e}")
            return False, f"Erro de banco de dados ao atualizar perfil: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar perfil: {e}")
            return False, f"Erro inesperado ao atualizar perfil: {str(e)}"

    @staticmethod
    def batch_pre_register_users(id_funcs, role):
        new_users_count = 0
        existing_users_count = 0
        
        for id_func in id_funcs:
            if not id_func.isdigit():
                current_app.logger.warning(f"ID Funcional inválido encontrado: {id_func}. Ignorando.")
                continue

            user_exists = db.session.execute(
                select(User).filter_by(id_func=id_func, role=role)
            ).scalar_one_or_none()

            if user_exists:
                existing_users_count += 1
            else:
                new_user = User(id_func=id_func, role=role, is_active=False)
                db.session.add(new_user)
                new_users_count += 1
        
        try:
            db.session.commit()
            return True, new_users_count, existing_users_count
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco de dados ao pré-cadastrar usuários em lote: {e}")
            return False, 0, 0
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao pré-cadastrar usuários em lote: {e}")
            return False, 0, 0
