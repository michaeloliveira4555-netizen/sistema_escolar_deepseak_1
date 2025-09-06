from ..models.database import db
from ..models.aluno import Aluno
from ..models.user import User
from ..models.historico import HistoricoAluno
from ..models.turma import Turma # Importa o modelo Turma
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from datetime import datetime

class AlunoService:
    @staticmethod
    def save_aluno(user_id, data):
        existing_aluno = db.session.execute(
            select(Aluno).where(Aluno.user_id == user_id)
        ).scalar_one_or_none()
        if existing_aluno:
            return False, "Este usuário já possui um perfil de aluno cadastrado."

        matricula = data.get('matricula')
        opm = data.get('opm')
        # O campo 'pelotao' foi substituído por 'turma_id'
        turma_id = data.get('turma_id')
        funcao_atual = data.get('funcao_atual')

        if not all([matricula, opm]):
            return False, "Todos os campos (Matrícula, OPM) são obrigatórios."

        try:
            novo_aluno = Aluno(
                user_id=user_id,
                matricula=matricula,
                opm=opm,
                turma_id=int(turma_id) if turma_id else None,
                funcao_atual=funcao_atual
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

    @staticmethod
    def get_all_alunos(nome_turma=None):
        stmt = select(Aluno).join(User)
        stmt = stmt.where(User.role != 'admin')
        
        # --- LÓGICA DE FILTRO ATUALIZADA ---
        if nome_turma:
            # Junta a tabela Aluno com a tabela Turma e filtra pelo nome da turma
            stmt = stmt.join(Turma).where(Turma.nome == nome_turma) 
            
        stmt = stmt.order_by(User.username)
        
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_aluno_by_id(aluno_id: int):
        return db.session.get(Aluno, aluno_id)

    @staticmethod
    def update_aluno(aluno_id: int, data: dict):
        aluno = db.session.get(Aluno, aluno_id)
        if not aluno:
            return False, "Aluno não encontrado."

        matricula = data.get('matricula')
        opm = data.get('opm')
        turma_id = data.get('turma_id')
        nova_funcao_atual = data.get('funcao_atual')

        if not all([matricula, opm]):
            return False, "Todos os campos (Matrícula, OPM) são obrigatórios."

        try:
            old_funcao = aluno.funcao_atual if aluno.funcao_atual else ''
            new_funcao = nova_funcao_atual if nova_funcao_atual else ''

            if old_funcao != new_funcao:
                descricao_log = f"Função alterada de '{old_funcao or 'N/A'}' para '{new_funcao or 'N/A'}'"
                log_historico = HistoricoAluno(
                    aluno_id=aluno.id,
                    tipo="Função Alterada",
                    descricao=descricao_log,
                    data_inicio=datetime.utcnow()
                )
                db.session.add(log_historico)

            aluno.matricula = matricula
            aluno.opm = opm
            aluno.turma_id = int(turma_id) if turma_id else None
            aluno.funcao_atual = nova_funcao_atual

            db.session.commit()
            return True, "Perfil do aluno atualizado com sucesso!"
        except IntegrityError:
            db.session.rollback()
            return False, "Erro de integridade dos dados. Verifique se a matrícula já está em uso."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar aluno: {e}")
            return False, f"Erro ao atualizar aluno: {str(e)}"