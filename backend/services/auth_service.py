from flask_login import login_user, logout_user, current_user
from sqlalchemy import select
from ..models.database import db
from ..models.user import User
from utils.validators import validate_username, validate_email, validate_password_strength

class AuthService:
    @staticmethod
    def login(username, password):
        stmt = select(User).where(User.username == username)
        user = db.session.scalar(stmt)

        if user and user.check_password(password) and getattr(user, 'is_active', False):
            login_user(user)
            return user
        return None

    @staticmethod
    def logout():
        logout_user()

    @staticmethod
    def register_user(data):
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            raise ValueError("Todos os campos (usuário, email, senha, confirmação) são obrigatórios.")
        
        if not validate_username(username):
            raise ValueError("Nome de usuário inválido. Deve ter entre 3 e 20 caracteres alfanuméricos.")
        if not validate_email(email):
            raise ValueError("Formato de e-mail inválido.")
        if password != confirm_password:
            raise ValueError("As senhas não coincidem.")
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            raise ValueError(message)

        if db.session.execute(select(User).where(User.username == username)).scalar_one_or_none():
            raise ValueError("Este nome de usuário já está em uso.")
        if db.session.execute(select(User).where(User.email == email)).scalar_one_or_none():
            raise ValueError("Este e-mail já está cadastrado.")

        new_user = User(username=username, email=email, role=data.get('role', 'aluno'))
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return new_user

    @staticmethod
    def is_admin():
        return current_user.is_authenticated and getattr(current_user, 'role', None) == 'admin'