from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.user import User
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.historico_disciplina import HistoricoDisciplina
from ..models.instrutor import Instrutor
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import current_app

class DisciplinaService:
    @staticmethod
    def get_disciplinas_com_instrutores(pelotao_filtrado):
        disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()
        disciplinas_com_instrutores = []
        if pelotao_filtrado:
            for disciplina in disciplinas:
                associacao = db.session.execute(
                    select(DisciplinaTurma).where(
                        DisciplinaTurma.disciplina_id == disciplina.id,
                        DisciplinaTurma.pelotao == pelotao_filtrado
                    )
                ).scalar_one_or_none()
                disciplinas_com_instrutores.append((disciplina, associacao))
        else:
            for disciplina in disciplinas:
                disciplinas_com_instrutores.append((disciplina, None))
        return disciplinas_com_instrutores

    @staticmethod
    def save_disciplina(form):
        try:
            nova_disciplina = Disciplina(
                materia=form.materia.data,
                carga_horaria_prevista=form.carga_horaria_prevista.data
            )
            db.session.add(nova_disciplina)
            db.session.commit()

            todos_os_alunos = db.session.scalars(select(Aluno)).all()
            for aluno in todos_os_alunos:
                nova_matricula = HistoricoDisciplina(aluno_id=aluno.id, disciplina_id=nova_disciplina.id)
                db.session.add(nova_matricula)
            
            turmas = db.session.scalars(select(Turma)).all()
            for turma in turmas:
                associacao = DisciplinaTurma(
                    pelotao=turma.nome,
                    disciplina_id=nova_disciplina.id
                )
                db.session.add(associacao)

            db.session.commit()
            return True, "Disciplina cadastrada e associada a todos os alunos e turmas!"
        except IntegrityError:
            db.session.rollback()
            return False, "Uma disciplina with this name already exists."
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
    def update_disciplina_com_instrutores(disciplina_id, form):
        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, "Disciplina não encontrada."

        try:
            disciplina.carga_horaria_prevista = form.carga_horaria.data
            
            atribuicoes_existentes = db.session.scalars(
                db.select(DisciplinaTurma).where(DisciplinaTurma.disciplina_id == disciplina.id)
            ).all()
            atribuicoes_map = {atr.pelotao: atr for atr in atribuicoes_existentes}

            for i in range(1, 9):
                pelotao_nome = f'{i}° Pelotão'
                instrutor_id_1_str = form[f'pelotao_{i}_instrutor_1'].data
                instrutor_id_2_str = form[f'pelotao_{i}_instrutor_2'].data

                instrutor_id_1 = int(instrutor_id_1_str) if instrutor_id_1_str and instrutor_id_1_str.isdigit() else None
                instrutor_id_2 = int(instrutor_id_2_str) if instrutor_id_2_str and instrutor_id_2_str.isdigit() else None

                associacao_existente = atribuicoes_map.get(pelotao_nome)

                if associacao_existente:
                    associacao_existente.instrutor_id_1 = instrutor_id_1
                    associacao_existente.instrutor_id_2 = instrutor_id_2
                elif instrutor_id_1 or instrutor_id_2:
                    nova_atribuicao = DisciplinaTurma(
                        pelotao=pelotao_nome,
                        disciplina_id=disciplina.id,
                        instrutor_id_1=instrutor_id_1,
                        instrutor_id_2=instrutor_id_2
                    )
                    db.session.add(nova_atribuicao)
            
            db.session.commit()
            return True, f'Atribuições da disciplina "{disciplina.materia}" atualizadas com sucesso!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar disciplina: {e}")
            return False, f"Erro inesperado ao atualizar disciplina: {str(e)}"