from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.user import User
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.historico_disciplina import HistoricoDisciplina
from ..models.horario import Horario
from ..models.instrutor import Instrutor
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
    @staticmethod
    def get_disciplinas_with_instrutores_for_pelotao(pelotao: str):
        query = (
            select(DisciplinaTurma)
            .options(
                joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.instrutor_2).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.disciplina)
            )
            .join(Disciplina)
            .filter(DisciplinaTurma.pelotao == pelotao)
            .order_by(Disciplina.materia)
        )
        return db.session.scalars(query).unique().all()

    @staticmethod
    def get_disciplinas_for_instrutor_in_pelotao(instrutor_id: int, pelotao: str):
        query = (
            select(DisciplinaTurma)
            .options(joinedload(DisciplinaTurma.disciplina))
            .where(
                DisciplinaTurma.pelotao == pelotao,
                or_(
                    DisciplinaTurma.instrutor_id_1 == instrutor_id,
                    DisciplinaTurma.instrutor_id_2 == instrutor_id
                )
            )
            .order_by(DisciplinaTurma.disciplina_id)
        )
        return db.session.scalars(query).unique().all()
        
    @staticmethod
    def save_disciplina(data):
        nome_materia = data.get('materia')
        carga_horaria = data.get('carga_horaria_prevista')

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        if db.session.execute(select(Disciplina).where(Disciplina.materia == nome_materia)).scalar_one_or_none():
            return False, "Uma disciplina com este nome já existe."

        nova_disciplina = Disciplina(
            materia=nome_materia,
            carga_horaria_prevista=carga_horaria_int
        )
        db.session.add(nova_disciplina)
        db.session.flush()  # Para obter o ID da nova disciplina

        # Matricula todos os alunos na nova disciplina
        todos_os_alunos = db.session.scalars(select(Aluno)).all()
        for aluno in todos_os_alunos:
            nova_matricula = HistoricoDisciplina(aluno_id=aluno.id, disciplina_id=nova_disciplina.id)
            db.session.add(nova_matricula)
        
        # Cria associações para todas as turmas
        turmas = db.session.scalars(select(Turma)).all()
        for turma in turmas:
            associacao = DisciplinaTurma(
                pelotao=turma.nome,
                disciplina_id=nova_disciplina.id,
            )
            db.session.add(associacao)

        return True, "Disciplina cadastrada e associada a todos os alunos e turmas!"

    @staticmethod
    def get_all_disciplinas():
        stmt = select(Disciplina).order_by(Disciplina.materia)
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_all_disciplinas_com_associacoes(pelotao: str = None):
        stmt = select(Disciplina).options(joinedload(Disciplina.associacoes_turmas)).order_by(Disciplina.materia)
        if pelotao:
            stmt = stmt.join(Disciplina.associacoes_turmas).where(DisciplinaTurma.pelotao == pelotao)
        return db.session.scalars(stmt).unique().all()

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

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        disciplina.materia = nome_materia
        disciplina.carga_horaria_prevista = carga_horaria_int
            
        return True, "Disciplina atualizada com sucesso!"

    @staticmethod
    def delete_disciplina(disciplina_id: int):
        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, "Disciplina não encontrada."
        
        try:
            # 1. Remover associações disciplina-turma
            db.session.query(DisciplinaTurma).filter_by(disciplina_id=disciplina_id).delete()
            
            # 2. Remover aulas agendadas
            db.session.query(Horario).filter_by(disciplina_id=disciplina_id).delete()
            
            # 3. Remover histórico de disciplinas dos alunos
            db.session.query(HistoricoDisciplina).filter_by(disciplina_id=disciplina_id).delete()
            
            # 4. Finalmente, remover a disciplina
            db.session.delete(disciplina)
            
            db.session.commit()
            return True, f'Disciplina "{disciplina.materia}" e todos os dados relacionados foram excluídos com sucesso!'
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao excluir disciplina: {e}")
            return False, f'Erro ao excluir disciplina: {str(e)}'