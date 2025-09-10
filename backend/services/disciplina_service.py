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
    def get_disciplinas_with_instrutores_for_pelotao(pelotao: str):
        """
        Busca todas as associações de disciplina para um pelotão específico,
        garantindo que os dados do instrutor e do usuário sejam pré-carregados.
        """
        print(f"DEBUG: Buscando disciplinas para pelotão: {pelotao}")
        
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
        
        associacoes = db.session.scalars(query).unique().all()
        
        print(f"DEBUG: Encontradas {len(associacoes)} associações")
        for a in associacoes:
            print(f"  - {a.disciplina.materia}: Instrutor1={a.instrutor_id_1}, Instrutor2={a.instrutor_id_2}")
            if a.instrutor_1:
                print(f"    Instrutor 1: {a.instrutor_1.user.nome_completo if a.instrutor_1.user else 'Sem user'}")
            if a.instrutor_2:
                print(f"    Instrutor 2: {a.instrutor_2.user.nome_completo if a.instrutor_2.user else 'Sem user'}")
        
        return associacoes
        
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

        existing_disciplina = db.session.execute(
            select(Disciplina).where(Disciplina.materia == nome_materia)
        ).scalar_one_or_none()
        if existing_disciplina:
            return False, "Uma disciplina com este nome já existe."

        try:
            nova_disciplina = Disciplina(
                materia=nome_materia,
                carga_horaria_prevista=carga_horaria_int
            )
            db.session.add(nova_disciplina)
            db.session.commit()

            # Matricula todos os alunos na nova disciplina
            todos_os_alunos = db.session.scalars(select(Aluno)).all()
            for aluno in todos_os_alunos:
                nova_matricula = HistoricoDisciplina(aluno_id=aluno.id, disciplina_id=nova_disciplina.id)
                db.session.add(nova_matricula)
            
            # Cria associações para todas as turmas (sem instrutores inicialmente)
            turmas = db.session.scalars(select(Turma)).all()
            for turma in turmas:
                associacao = DisciplinaTurma(
                    pelotao=turma.nome,
                    disciplina_id=nova_disciplina.id,
                    instrutor_id_1=None,  # Será definido posteriormente
                    instrutor_id_2=None   # Será definido posteriormente
                )
                db.session.add(associacao)

            db.session.commit()
            print(f"DEBUG: Disciplina '{nome_materia}' criada e associada a todas as turmas")
            return True, "Disciplina cadastrada e associada a todos os alunos e turmas!"
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

        if not nome_materia or not carga_horaria:
            return False, "Matéria e Carga Horária são campos obrigatórios."

        try:
            carga_horaria_int = int(carga_horaria)
        except (ValueError, TypeError):
            return False, "Carga horária deve ser um número inteiro."

        try:
            disciplina.materia = nome_materia
            disciplina.carga_horaria_prevista = carga_horaria_int
            
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
    def verificar_associacoes_disciplinas():
        """
        Método de debug para verificar todas as associações disciplina-turma
        """
        print("=== DEBUG: Verificando todas as associações disciplina-turma ===")
        
        query = (
            select(DisciplinaTurma)
            .options(
                joinedload(DisciplinaTurma.disciplina),
                joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.instrutor_2).joinedload(Instrutor.user)
            )
            .order_by(DisciplinaTurma.pelotao, DisciplinaTurma.disciplina_id)
        )
        
        todas_associacoes = db.session.scalars(query).unique().all()
        
        for assoc in todas_associacoes:
            print(f"Pelotão: {assoc.pelotao}")
            print(f"  Disciplina: {assoc.disciplina.materia}")
            print(f"  Instrutor 1 ID: {assoc.instrutor_id_1}")
            if assoc.instrutor_1:
                nome1 = assoc.instrutor_1.user.nome_completo if assoc.instrutor_1.user else "Sem usuário"
                print(f"    Nome: {nome1}")
            print(f"  Instrutor 2 ID: {assoc.instrutor_id_2}")
            if assoc.instrutor_2:
                nome2 = assoc.instrutor_2.user.nome_completo if assoc.instrutor_2.user else "Sem usuário"
                print(f"    Nome: {nome2}")
            print("---")
        
        print(f"Total de associações: {len(todas_associacoes)}")
        return todas_associacoes