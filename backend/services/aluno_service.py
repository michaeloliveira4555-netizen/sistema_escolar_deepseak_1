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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _save_profile_picture(file):
    if file:
        file.stream.seek(0) # Reset stream position before reading magic bytes
        if allowed_file(file.filename, file.stream, ALLOWED_EXTENSIONS):
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
    def save_aluno(user_id, data, foto_perfil=None):
        existing_aluno = db.session.execute(
            select(Aluno).where(Aluno.user_id == user_id)
        ).scalar_one_or_none()
        if existing_aluno:
            return False, "Este usuário já possui um perfil de aluno cadastrado."

        matricula = data.get('matricula')
        opm = data.get('opm')
        turma_id = data.get('turma_id')
        funcao_atual = data.get('funcao_atual')

        if not all([matricula, opm]):
            return False, "Todos os campos (Matrícula, OPM) são obrigatórios."

        try:
            foto_filename = _save_profile_picture(foto_perfil)

            novo_aluno = Aluno(
                user_id=user_id,
                matricula=matricula,
                opm=opm,
                turma_id=int(turma_id) if turma_id else None,
                funcao_atual=funcao_atual,
                foto_perfil=foto_filename if foto_filename else 'default.png'
            )
            db.session.add(novo_aluno)
            db.session.commit()

            # LÓGICA DE MATRÍCULA AUTOMÁTICA
            todas_as_disciplinas = db.session.scalars(select(Disciplina)).all()
            for disciplina in todas_as_disciplinas:
                # Verifica se a matrícula já não existe por algum motivo
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
    def update_aluno(aluno_id: int, data: dict, foto_perfil=None):
        aluno = db.session.get(Aluno, aluno_id)
        if not aluno:
            return False, "Aluno não encontrado."

        nome_completo = data.get('nome_completo')
        matricula = data.get('matricula')
        opm = data.get('opm')
        turma_id_val = data.get('turma_id')
        nova_funcao_atual = data.get('funcao_atual')

        if not all([nome_completo, matricula, opm]) or turma_id_val in (None, ''):
            return False, "Nome, Matrícula, OPM e Turma são campos obrigatórios."

        try:
            # Conversão segura do ID da turma para inteiro (aceita int ou str)
            try:
                nova_turma_id = int(turma_id_val) if turma_id_val not in (None, '') else None
            except (ValueError, TypeError):
                nova_turma_id = None

            # Lógica de histórico refatorada
            alteracoes = []
            if aluno.user and aluno.user.nome_completo != nome_completo:
                alteracoes.append(f"Nome alterado de '{aluno.user.nome_completo or 'N/A'}' para '{nome_completo or 'N/A'}'")
            if aluno.matricula != matricula:
                alteracoes.append(f"Matrícula alterada de '{aluno.matricula or 'N/A'}' para '{matricula or 'N/A'}'")
            if aluno.opm != opm:
                alteracoes.append(f"OPM alterada de '{aluno.opm or 'N/A'}' para '{opm or 'N/A'}'")
            if aluno.turma_id != nova_turma_id:
                turma_antiga = db.session.get(Turma, aluno.turma_id) if aluno.turma_id else None
                nova_turma = db.session.get(Turma, nova_turma_id) if nova_turma_id else None
                alteracoes.append(f"Turma alterada de '{turma_antiga.nome if turma_antiga else 'N/A'}' para '{nova_turma.nome if nova_turma else 'N/A'}'")
            
            old_funcao = aluno.funcao_atual or ''
            new_funcao = nova_funcao_atual or ''
            if old_funcao != new_funcao:
                alteracoes.append(f"Função alterada de '{old_funcao or 'N/A'}' para '{new_funcao or 'N/A'}'")

            if alteracoes:
                log_historico = HistoricoAluno(
                    aluno_id=aluno.id,
                    tipo="Perfil Atualizado",
                    descricao="; ".join(alteracoes),
                    data_inicio=datetime.utcnow()
                )
                db.session.add(log_historico)

            # Atualiza os dados do aluno
            if aluno.user:
                aluno.user.nome_completo = nome_completo
            aluno.matricula = matricula
            aluno.opm = opm
            aluno.turma_id = nova_turma_id
            aluno.funcao_atual = nova_funcao_atual

            if foto_perfil and hasattr(foto_perfil, 'filename') and foto_perfil.filename != '':
                foto_filename = _save_profile_picture(foto_perfil)
                if foto_filename:
                    aluno.foto_perfil = foto_filename

            db.session.commit()
            return True, "Perfil do aluno atualizado com sucesso!"

        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matrícula já está em uso."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar aluno: {e}")
            return False, f"Ocorreu um erro inesperado ao atualizar o perfil. Detalhes: {str(e)}"

    @staticmethod
    def delete_aluno(aluno_id: int):
        aluno = db.session.get(Aluno, aluno_id)
        if not aluno:
            return False, "Aluno não encontrado."

        try:
            # A exclusão do usuário irá acionar a exclusão em cascata
            # do perfil do aluno associado, graças à configuração no modelo User.
            user_a_deletar = aluno.user
            db.session.delete(user_a_deletar)
            db.session.commit()
            return True, "Aluno excluído com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir aluno: {e}")
            return False, f"Erro ao excluir aluno: {str(e)}"