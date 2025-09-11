from ..models.database import db
from ..models.user import User
from sqlalchemy import select

class UserService:
    @staticmethod
    def pre_register_user(form):
        try:
            user_exists = db.session.execute(db.select(User).filter_by(id_func=form.id_func.data)).scalar_one_or_none()
            
            if user_exists:
                return False, f'A Id Func "{form.id_func.data}" já está pré-cadastrada no sistema.'

            new_user = User(
                id_func=form.id_func.data,
                role=form.role.data,
                is_active=False
            )
            db.session.add(new_user)
            db.session.commit()
            return True, f'Usuário com Id Func "{form.id_func.data}" pré-cadastrado com sucesso!'
        except Exception as e:
            db.session.rollback()
            return False, f'Erro ao pré-cadastrar usuário: {e}'