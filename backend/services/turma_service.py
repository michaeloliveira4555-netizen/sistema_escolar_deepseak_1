from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.turma_cargo import TurmaCargo
from sqlalchemy import select, or_

CARGOS_LISTA = [
    "Auxiliar do Pelotão", "Chefe de Turma", "C1", "C2", "C3", "C4", "C5"
]

class TurmaService:
    @staticmethod
    def get_all_turmas():
        return db.session.scalars(select(Turma).order_by(Turma.nome)).all()

    @staticmethod
    def get_turma_by_id(turma_id):
        return db.session.get(Turma, turma_id)

    @staticmethod
    def get_cargos_by_turma(turma_id):
        cargos_db = db.session.scalars(
            select(TurmaCargo).where(TurmaCargo.turma_id == turma_id)
        ).all()
        cargos_atuais = {cargo.cargo_nome: cargo.aluno_id for cargo in cargos_db}
        for cargo in CARGOS_LISTA:
            if cargo not in cargos_atuais:
                cargos_atuais[cargo] = None
        return cargos_atuais

    @staticmethod
    def save_cargos_turma(turma_id, form):
        try:
            for cargo_nome in CARGOS_LISTA:
                aluno_id = form[f'cargo_{cargo_nome}'].data
                cargo_existente = db.session.scalars(
                    select(TurmaCargo).where(
                        TurmaCargo.turma_id == turma_id,
                        TurmaCargo.cargo_nome == cargo_nome
                    )
                ).first()

                if cargo_existente:
                    cargo_existente.aluno_id = aluno_id
                else:
                    novo_cargo = TurmaCargo(
                        turma_id=turma_id,
                        cargo_nome=cargo_nome,
                        aluno_id=aluno_id
                    )
                    db.session.add(novo_cargo)
            
            db.session.commit()
            return True, 'Cargos da turma atualizados com sucesso!'
        except Exception as e:
            db.session.rollback()
            return False, f'Erro ao salvar os cargos: {e}'

    @staticmethod
    def create_turma(form):
        try:
            turma_existente = db.session.execute(
                select(Turma).filter_by(nome=form.nome.data)
            ).scalar_one_or_none()

            if turma_existente:
                return False, f'Uma turma com o nome "{form.nome.data}" já existe.'

            nova_turma = Turma(nome=form.nome.data, ano=form.ano.data)
            db.session.add(nova_turma)
            db.session.commit() 

            if form.alunos_ids.data:
                for aluno_id in form.alunos_ids.data:
                    aluno = db.session.get(Aluno, int(aluno_id))
                    if aluno:
                        aluno.turma_id = nova_turma.id
                db.session.commit()
            
            return True, 'Turma cadastrada com sucesso!'
        except Exception as e:
            db.session.rollback()
            return False, f'Erro ao cadastrar turma: {e}'

    @staticmethod
    def get_alunos_sem_turma():
        return db.session.scalars(
            select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0))
        ).all()