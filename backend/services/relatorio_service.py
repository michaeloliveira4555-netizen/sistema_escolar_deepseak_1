from ..models.database import db
from ..models.horario import Horario
from ..models.semana import Semana
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from ..models.user import User
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from collections import defaultdict

class RelatorioService:
    @staticmethod
    def get_horas_aula_por_instrutor(data_inicio, data_fim, is_rr_filter=False, instrutor_ids_filter=None):
        """
        Busca e totaliza as horas-aula por instrutor e disciplina,
        com filtros opcionais para RR e IDs de instrutores.
        """
        semanas_no_periodo = db.session.scalars(
            select(Semana.id).where(
                and_(
                    Semana.data_inicio <= data_fim,
                    Semana.data_fim >= data_inicio
                )
            )
        ).all()

        query_a_pagar = (
            select(
                Horario.instrutor_id,
                Horario.disciplina_id,
                func.sum(Horario.duracao).label('total_horas')
            )
            .join(Instrutor, Horario.instrutor_id == Instrutor.id)
            .where(
                Horario.semana_id.in_(semanas_no_periodo_atual),
                Horario.status == 'confirmado'
            )
        )
        
        if is_rr_filter:
            query_a_pagar = query_a_pagar.where(Instrutor.is_rr == True)
        
        if instrutor_ids_filter:
            query_a_pagar = query_a_pagar.where(Horario.instrutor_id.in_(instrutor_ids_filter))

        aulas_a_pagar = db.session.execute(
            query_a_pagar.group_by(Horario.instrutor_id, Horario.disciplina_id)
        ).all()

        aulas = db.session.execute(
            select(
                Horario.instrutor_id,
                Horario.disciplina_id,
                func.sum(Horario.duracao).label('total_horas')
            ).where(
                Horario.semana_id.in_(semanas_periodo_anterior),
                Horario.status == 'confirmado'
            ).group_by(Horario.instrutor_id, Horario.disciplina_id)
        ).all()
        
        mapa_ch_paga = {
            (aula.instrutor_id, aula.disciplina_id): aula.total_horas
            for aula in aulas_pagas_anteriormente
        }

        # Pré-carrega instrutores e disciplinas para evitar N+1
        instrutor_ids = [aula.instrutor_id for aula in aulas]
        disciplina_ids = [aula.disciplina_id for aula in aulas]

        instrutores_map = {inst.id: inst for inst in db.session.scalars(
            select(Instrutor).options(joinedload(Instrutor.user)).where(Instrutor.id.in_(instrutor_ids))
        ).all()}
        disciplinas_map = {disc.id: disc for disc in db.session.scalars(
            select(Disciplina).where(Disciplina.id.in_(disciplina_ids))
        ).all()}

        instrutores_dados = defaultdict(lambda: {
            'info': None,
            'disciplinas': []
        })

        for aula in aulas:
            instrutor = instrutores_map.get(aula.instrutor_id)
            disciplina = disciplinas_map.get(aula.disciplina_id)

            if instrutor:
                instrutores_dados[instrutor.id]['info'] = instrutor
                
                disciplina_info = {
                    'nome': disciplina.materia if disciplina else "Disciplina não encontrada",
                    'horas': aula.total_horas
                }
                
                instrutores_dados[instrutor.id]['disciplinas'].append(disciplina_info)
                instrutores_dados[instrutor.id]['total_geral'] += aula.total_horas
        
        # Converte o dicionário para uma lista ordenada por nome do instrutor
        # Garante que instrutor.user exista antes de acessar nome_completo
        resultado_final = sorted(
            [data for data in instrutores_dados.values() if data['info'] and data['info'].user],
            key=lambda x: x['info'].user.nome_completo or ""
        )
        
        return resultado_final