from ..extensions import db
from ..models.aluno import Aluno
from ..models.user import User
from ..models.historico import HistoricoAluno
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

class AlunoService:

    @staticmethod
    def _save_photo(photo_file):
        if not photo_file or photo_file.filename == '':
            return None, "Nenhum arquivo de foto enviado."

        allowed_extensions = {'png', 'jpg', 'jpeg'}
        filename = secure_filename(photo_file.filename)
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return None, "Formato de arquivo de foto inválido. Use png, jpg ou jpeg."

        unique_filename = f"{uuid.uuid4().hex}.{filename.rsplit('.', 1)[1].lower()}"
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        os.makedirs(upload_folder, exist_ok=True)
        
        photo_path = os.path.join(upload_folder, unique_filename)
        photo_file.save(photo_path)
        
        return unique_filename, "Foto salva com sucesso."

    @staticmethod
    def save_aluno(user_id, data, photo_file=None):
        try:
            foto_filename = None
            if photo_file:
                foto_filename, message = AlunoService._save_photo(photo_file)
                if not foto_filename:
                    return False, message

            novo_aluno = Aluno(
                user_id=user_id,
                nome_completo=data.get('nome_completo'),
                matricula=data.get('matricula'),
                opm=data.get('opm'),
                pelotao=data.get('pelotao'),
                funcao_atual=data.get('funcao_atual'),
                foto_perfil=foto_filename
            )
            db.session.add(novo_aluno)
            db.session.commit()
            return True, "Perfil de aluno cadastrado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matrícula já está em uso."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao cadastrar aluno: {e}")
            return False, f"Erro ao cadastrar aluno: {str(e)}"

    # --- FUNÇÃO QUE FALTAVA ---
    @staticmethod
    def get_all_alunos(pelotao_filtrado=None):
        stmt = select(Aluno).order_by(Aluno.nome_completo)
        
        if pelotao_filtrado:
            stmt = stmt.where(Aluno.pelotao == pelotao_filtrado) 
            
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def get_aluno_by_id(aluno_id: int):
        return db.session.get(Aluno, aluno_id)

    @staticmethod
    def update_aluno(aluno_id: int, data: dict, photo_file=None):
        try:
            aluno = AlunoService.get_aluno_by_id(aluno_id)
            if not aluno:
                return False, "Aluno não encontrado."

            if photo_file:
                foto_filename, message = AlunoService._save_photo(photo_file)
                if not foto_filename:
                    return False, message
                aluno.foto_perfil = foto_filename

            if aluno.funcao_atual != data.get('funcao_atual'):
                descricao_log = f"Função alterada de '{aluno.funcao_atual or 'N/A'}' para '{data.get('funcao_atual') or 'N/A'}'"
                log_historico = HistoricoAluno(
                    aluno_id=aluno.id,
                    tipo="Função Alterada",
                    descricao=descricao_log,
                    data_inicio=datetime.utcnow()
                )
                db.session.add(log_historico)

            aluno.nome_completo = data.get('nome_completo')
            aluno.matricula = data.get('matricula')
            aluno.opm = data.get('opm')
            aluno.pelotao = data.get('pelotao')
            aluno.funcao_atual = data.get('funcao_atual')

            if aluno.user:
                aluno.user.email = data.get('email')
                aluno.user.matricula = data.get('matricula')
                aluno.user.username = data.get('matricula')

            db.session.commit()
            return True, "Perfil do aluno atualizado com sucesso!"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao atualizar aluno: {str(e)}"
    
    @staticmethod
    def delete_aluno(aluno_id):
        try:
            aluno = AlunoService.get_aluno_by_id(aluno_id)
            if not aluno:
                return False, "Aluno não encontrado."
            
            user = aluno.user
            db.session.delete(user)
            db.session.commit()
            return True, "Aluno e usuário associado foram removidos com sucesso."
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao remover aluno: {e}"