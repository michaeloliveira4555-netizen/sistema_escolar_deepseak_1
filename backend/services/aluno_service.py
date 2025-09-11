import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from ..models.database import db
from ..models.aluno import Aluno
from ..models.user import User
from ..models.historico import HistoricoAluno
from ..models.turma import Turma
from ..models.disciplina import Disciplina
from ..models.historico_disciplina import HistoricoDisciplina
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from utils.image_utils import allowed_file

def _save_profile_picture(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{ext}"
        
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile_pics')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

class AlunoService:
    @staticmethod
    def create_aluno_with_user(form):
        try:
            user_exists_id_func = db.session.execute(db.select(User).filter_by(id_func=form.matricula.data)).scalar_one_or_none()
            if user_exists_id_func:
                return False, 'Esta matrícula (Id Funcional) já está em uso.'

            new_user = User(
                id_func=form.matricula.data,
                username=form.matricula.data, 
                nome_completo=form.nome_completo.data,
                email=form.email.data, 
                role='aluno',
                is_active=True
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()

            success, message = AlunoService.save_aluno(new_user.id, form)

            if not success:
                db.session.delete(new_user)
                db.session.commit()
                return False, message

            return True, "Aluno cadastrado com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar aluno: {e}")
            return False, f"Erro ao cadastrar aluno: {str(e)}"

    @staticmethod
    def save_aluno(user_id, form, foto_perfil=None):
        existing_aluno = db.session.execute(
            select(Aluno).where(Aluno.user_id == user_id)
        ).scalar_one_or_none()
        if existing_aluno:
            return False, "Este usuário já possui um perfil de aluno cadastrado."

        try:
            foto_filename = _save_profile_picture(foto_perfil)

            novo_aluno = Aluno(
                user_id=user_id,
                matricula=form.matricula.data,
                opm=form.opm.data,
                turma_id=form.turma_id.data,
                funcao_atual=form.funcao_atual.data,
                foto_perfil=foto_filename if foto_filename else 'default.png'
            )
            db.session.add(novo_aluno)
            db.session.commit()

            todas_as_disciplinas = db.session.scalars(select(Disciplina)).all()
            for disciplina in todas_as_disciplinas:
                matricula_existente = db.session.execute(
                    select(HistoricoDisciplina).where(
                        HistoricoDisciplina.aluno_id == novo_aluno.id,
                        HistoricoDisciplina.disciplina_id == disciplina.id
                    )
                ).scalar_one_or_none()
                if not matricula_existente:
                    nova_matricula = HistoricoDisciplina(aluno_id=novo_aluno.id, disciplina_id=disciplina.id)
                    db.session.add(nova_matricula)
            
            db.session.commit()
            return True, "Perfil de aluno cadastrado e matriculado em todas as disciplinas!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matrícula já está em uso."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar aluno: {e}")
            return False, f"Erro ao cadastrar aluno: {str(e)}"

    @staticmethod
    def get_all_alunos(nome_turma=None):
        stmt = select(Aluno).join(User)
        stmt = stmt.where(User.role != 'admin')
        
        if nome_turma:
            stmt = stmt.join(Turma).where(Turma.nome == nome_turma) 
            
        stmt = stmt.order_by(User.username)
        
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_aluno_by_id(aluno_id: int):
        return db.session.get(Aluno, aluno_id)

    @staticmethod
    def update_aluno(aluno_id: int, form, foto_perfil=None):
        aluno = db.session.get(Aluno, aluno_id)
        if not aluno:
            return False, "Aluno não encontrado."

        try:
            old_funcao = aluno.funcao_atual if aluno.funcao_atual else ''
            new_funcao = form.funcao_atual.data if form.funcao_atual.data else ''

            if old_funcao != new_funcao:
                descricao_log = f"Função alterada de '{old_funcao or 'N/A'}' para '{new_funcao or 'N/A'}'"
                log_historico = HistoricoAluno(
                    aluno_id=aluno.id,
                    tipo="Função Alterada",
                    descricao=descricao_log,
                    data_inicio=datetime.utcnow()
                )
                db.session.add(log_historico)

            if aluno.user:
                aluno.user.nome_completo = form.nome_completo.data
            
            if foto_perfil:
                foto_filename = _save_profile_picture(foto_perfil)
                aluno.foto_perfil = foto_filename
            
            aluno.matricula = form.matricula.data
            aluno.opm = form.opm.data
            aluno.turma_id = form.turma_id.data
            aluno.funcao_atual = new_funcao

            db.session.commit()
            return True, "Perfil do aluno atualizado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matrícula já está em uso."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar aluno: {e}")
            return False, f"Erro ao atualizar aluno: {str(e)}"