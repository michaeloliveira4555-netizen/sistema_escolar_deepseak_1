from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
    @staticmethod
    def save_disciplina(data):
        nome_materia = data.get('materia')
        carga_horaria = data.get('carga_horaria_prevista')
        # A linha abaixo que pegava o instrutor_id não é mais necessária aqui, mas podemos deixar
        instrutor_id = data.get('instrutor_id')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        existing_disciplina = db.session.execute(
            select(Disciplina).where(Disciplina.materia == nome_materia)
        ).scalar_one_or_none()
        if existing_disciplina:
            return False, "Uma disciplina com este nome já existe."

        try:
            # --- CORREÇÃO AQUI ---
            # Removemos o argumento 'instrutor_id' que não existe mais no modelo Disciplina
            nova_disciplina = Disciplina(
                materia=nome_materia,
                carga_horaria_prevista=carga_horaria_int
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
        # A linha abaixo que pegava o instrutor_id não é mais necessária aqui
        instrutor_id = data.get('instrutor_id')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        try:
            disciplina.materia = nome_materia
            disciplina.carga_horaria_prevista = carga_horaria_int
            # A linha que atualizava o instrutor_id também foi removida
            
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
        # Esta função pode ser reavaliada ou removida, pois a lógica de atribuição mudou
        # Por enquanto, vamos mantê-la inalterada para não quebrar outras partes do código
        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, "Disciplina não encontrada."
        
        user = db.session.get(User, instrutor_user_id)
        
        if user and user.instrutor_profile:
            # Esta lógica precisará ser adaptada para a nova tabela 'DisciplinaTurma'
            # No momento, ela não terá efeito prático no novo modelo
            pass
        return False, "Lógica de atribuição de instrutor foi movida para a tela de gerenciamento de disciplina."


    @staticmethod
    def remove_instrutor_from_disciplina(instrutor_user_id: int):
        # Esta função também precisa ser reavaliada
        user = db.session.get(User, instrutor_user_id)
        
        if user and user.instrutor_profile:
            # A lógica para desvincular um instrutor agora deve acontecer na tabela 'DisciplinaTurma'
            pass
        return False, "Lógica de desvinculação de instrutor foi movida."