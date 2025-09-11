from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.turma_cargo import TurmaCargo
from sqlalchemy import select
from flask import current_app

class TurmaService:
    @staticmethod
    def create_turma(data):
        nome_turma = data.get('nome')
        ano = data.get('ano')
        alunos_ids = data.getlist('alunos_ids')

        if not nome_turma or not ano:
            return False, 'Nome da turma e ano são obrigatórios.'

        if db.session.execute(select(Turma).filter_by(nome=nome_turma)).scalar_one_or_none():
            return False, f'Uma turma com o nome "{nome_turma}" já existe.'

        try:
            nova_turma = Turma(nome=nome_turma, ano=int(ano))
            db.session.add(nova_turma)
            db.session.flush()  # Para obter o ID da nova turma

            if alunos_ids:
                for aluno_id in alunos_ids:
                    aluno = db.session.get(Aluno, int(aluno_id))
                    if aluno:
                        aluno.turma_id = nova_turma.id
            
            db.session.commit()
            return True, "Turma cadastrada com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao criar turma: {e}")
            return False, f"Erro ao criar turma: {str(e)}"

    @staticmethod
    def delete_turma(turma_id):
        turma = db.session.get(Turma, turma_id)
        if not turma:
            return False, 'Turma não encontrada.'

        try:
            nome_turma_excluida = turma.nome
            # Desvincula alunos
            for aluno in turma.alunos:
                aluno.turma_id = None
            
            # Exclui cargos e associações
            db.session.query(TurmaCargo).filter_by(turma_id=turma_id).delete()
            db.session.query(DisciplinaTurma).filter_by(pelotao=turma.nome).delete()
            
            db.session.delete(turma)
            db.session.commit()
            return True, f'Turma "{nome_turma_excluida}" e todos os seus vínculos foram excluídos com sucesso!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir turma: {e}")
            return False, f'Erro ao excluir a turma: {str(e)}'
