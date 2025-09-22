# backend/services/turma_service.py

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
        alunos_ids = data.getlist('alunos_ids') if hasattr(data, 'getlist') else data.get('alunos_ids', [])

        if not nome_turma or not ano:
            return False, 'Nome da turma e ano são obrigatórios.'

        if db.session.execute(select(Turma).filter_by(nome=nome_turma)).scalar_one_or_none():
            return False, f'Uma turma com o nome "{nome_turma}" já existe.'

        try:
            nova_turma = Turma(nome=nome_turma, ano=int(ano))
            db.session.add(nova_turma)
            db.session.flush()

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
    def update_turma(turma_id, form):
        """Atualiza os dados de uma turma e a lista de seus alunos."""
        turma = db.session.get(Turma, turma_id)
        if not turma:
            return False, "Turma não encontrada."
            
        novo_nome = form.nome.data
        # Verifica se o novo nome já existe em OUTRA turma
        if db.session.execute(select(Turma).where(Turma.nome == novo_nome, Turma.id != turma_id)).scalar_one_or_none():
            return False, f'Já existe outra turma com o nome "{novo_nome}".'
            
        try:
            turma.nome = novo_nome
            turma.ano = form.ano.data
            
            # Desvincula todos os alunos que atualmente pertencem à turma
            db.session.query(Aluno).filter(Aluno.turma_id == turma_id).update({"turma_id": None})
            
            # Vincula os novos alunos selecionados no formulário
            if form.alunos_ids.data:
                db.session.query(Aluno).filter(Aluno.id.in_(form.alunos_ids.data)).update({"turma_id": turma_id})
                
            db.session.commit()
            return True, "Turma atualizada com sucesso!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao atualizar turma: {e}")
            return False, f"Erro ao atualizar turma: {str(e)}"

    @staticmethod
    def delete_turma(turma_id):
        turma = db.session.get(Turma, turma_id)
        if not turma:
            return False, 'Turma não encontrada.'

        try:
            nome_turma_excluida = turma.nome
            # Desvincula alunos (redundante, mas seguro)
            for aluno in turma.alunos:
                aluno.turma_id = None
            
            # Exclui cargos e associações de disciplinas
            db.session.query(TurmaCargo).filter_by(turma_id=turma_id).delete()
            db.session.query(DisciplinaTurma).filter_by(pelotao=turma.nome).delete()
            
            db.session.delete(turma)
            db.session.commit()
            return True, f'Turma "{nome_turma_excluida}" e todos os seus vínculos foram excluídos com sucesso!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir turma: {e}")
            return False, f'Erro ao excluir a turma: {str(e)}'

    @staticmethod
    def get_cargos_da_turma(turma_id, cargos_lista):
        """Busca os cargos de uma turma e garante que todos da lista existam."""
        cargos_db = db.session.scalars(
            select(TurmaCargo).where(TurmaCargo.turma_id == turma_id)
        ).all()
        cargos_atuais = {cargo.cargo_nome: cargo.aluno_id for cargo in cargos_db}

        # Garante que todos os cargos da lista padrão estejam no dicionário
        for cargo in cargos_lista:
            if cargo not in cargos_atuais:
                cargos_atuais[cargo] = None
        return cargos_atuais

    @staticmethod
    def atualizar_cargos(turma_id, form_data):
        """Cria ou atualiza os cargos de uma turma com base nos dados do formulário."""
        from ..controllers.turma_controller import CARGOS_LISTA
        
        if not db.session.get(Turma, turma_id):
            return False, 'Turma não encontrada.'
        
        try:
            for cargo_nome in CARGOS_LISTA:
                aluno_id_str = form_data.get(f'cargo_{cargo_nome}')
                aluno_id = int(aluno_id_str) if aluno_id_str else None

                cargo_existente = db.session.scalars(
                    select(TurmaCargo).where(
                        TurmaCargo.turma_id == turma_id,
                        TurmaCargo.cargo_nome == cargo_nome
                    )
                ).first()

                if cargo_existente:
                    cargo_existente.aluno_id = aluno_id
                elif aluno_id:
                    novo_cargo = TurmaCargo(turma_id=turma_id, cargo_nome=cargo_nome, aluno_id=aluno_id)
                    db.session.add(novo_cargo)
            
            db.session.commit()
            return True, 'Cargos da turma atualizados com sucesso!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar os cargos: {e}")
            return False, 'Erro interno ao salvar os cargos.'