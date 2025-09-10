from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.horario import Horario

class HorarioService:
    @staticmethod
    def get_scheduling_data(pelotao: str, user):
        """
        Busca os dados necessários para o agendamento de aulas,
        respeitando as permissões do usuário.
        """
        is_admin = user.role in ['admin', 'programador']
        instrutor_id = user.instrutor_profile.id if hasattr(user, 'instrutor_profile') and user.instrutor_profile else None

        # --- Lógica para Administradores ---
        if is_admin:
            # Admin vê todas as disciplinas da turma e todos os instrutores do sistema
            disciplinas_query = (
                select(DisciplinaTurma)
                .options(joinedload(DisciplinaTurma.disciplina))
                .join(Disciplina)
                .filter(DisciplinaTurma.pelotao == pelotao)
                .order_by(Disciplina.materia)
            )
            todos_instrutores_query = (
                select(Instrutor)
                .options(joinedload(Instrutor.user))
                .order_by(Instrutor.id)
            )
            
            associacoes = db.session.scalars(disciplinas_query).unique().all()
            todos_instrutores = db.session.scalars(todos_instrutores_query).all()
            
            # Formata todos os instrutores para o template
            instrutores_formatados = [{
                "id": instrutor.id,
                "nome": instrutor.user.nome_completo or instrutor.user.username
            } for instrutor in todos_instrutores]

        # --- Lógica para Instrutores ---
        else:
            # Instrutor vê apenas as disciplinas às quais está vinculado
            query = (
                select(DisciplinaTurma)
                .options(
                    joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
                    joinedload(DisciplinaTurma.instrutor_2).joinedload(Instrutor.user),
                    joinedload(DisciplinaTurma.disciplina)
                )
                .join(Disciplina)
                .filter(
                    DisciplinaTurma.pelotao == pelotao,
                    (DisciplinaTurma.instrutor_id_1 == instrutor_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_id)
                )
                .order_by(Disciplina.materia)
            )
            associacoes = db.session.scalars(query).unique().all()
            instrutores_formatados = None # Instrutor não escolhe, o sistema define

        # --- Preparação dos dados para o Template ---
        disciplinas_disponiveis = []
        for a in associacoes:
            total_previsto = a.disciplina.carga_horaria_prevista
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(
                disciplina_id=a.disciplina.id, 
                pelotao=pelotao,
                status='confirmado'
            ).scalar() or 0
            
            # Para instrutores, determina qual instrutor está logado
            instrutor_principal_id = a.instrutor_id_1 if (is_admin or a.instrutor_id_1 == instrutor_id) else a.instrutor_id_2
            instrutor_principal_nome = None
            if a.instrutor_1 and (is_admin or a.instrutor_id_1 == instrutor_id) and a.instrutor_1.user:
                 instrutor_principal_nome = a.instrutor_1.user.nome_completo or a.instrutor_1.user.username
            elif a.instrutor_2 and (is_admin or a.instrutor_id_2 == instrutor_id) and a.instrutor_2.user:
                instrutor_principal_nome = a.instrutor_2.user.nome_completo or a.instrutor_2.user.username

            disciplinas_disponiveis.append({
                "id": a.disciplina.id,
                "nome": a.disciplina.materia,
                "instrutor_padrao_id": instrutor_principal_id,
                "instrutor_padrao_nome": instrutor_principal_nome,
                "carga_restante": total_previsto - horas_agendadas
            })
            
        return disciplinas_disponiveis, instrutores_formatados