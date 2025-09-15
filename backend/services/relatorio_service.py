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
        
        semanas_no_periodo_atual = db.session.scalars(
            select(Semana.id).where(and_(Semana.data_inicio <= data_fim, Semana.data_fim >= data_inicio))
        ).all()
        
        semanas_periodo_anterior = db.session.scalars(
            select(Semana.id).where(Semana.data_inicio < data_inicio)
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

        aulas_pagas_anteriormente = db.session.execute(
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

        instrutores_dados = defaultdict(lambda: {
            'info': None,
            'disciplinas': []
        })

        for aula in aulas_a_pagar:
            instrutor_id = aula.instrutor_id
            disciplina_id = aula.disciplina_id
            
            if not instrutores_dados[instrutor_id]['info']:
                instrutor = db.session.get(Instrutor, instrutor_id)
                if instrutor:
                    instrutores_dados[instrutor_id]['info'] = instrutor

            disciplina = db.session.get(Disciplina, disciplina_id)
            ch_total = disciplina.carga_horaria_prevista if disciplina else 0
            
            ch_paga_anteriormente = mapa_ch_paga.get((instrutor_id, disciplina_id), 0)

            disciplina_info = {
                'nome': disciplina.materia if disciplina else "Disciplina não encontrada",
                'ch_total': ch_total,
                'ch_paga_anteriormente': ch_paga_anteriormente,
                'ch_a_pagar': aula.total_horas,
            }
            
            instrutores_dados[instrutor_id]['disciplinas'].append(disciplina_info)
        
        # Converte para lista e ordena pela Id. Func. do usuário associado
        resultado_final = sorted(
            instrutores_dados.values(), 
            key=lambda x: (int(x['info'].user.id_func) if x['info'] and x['info'].user and x['info'].user.id_func.isdigit() else float('inf'))
        )
        
        return resultado_final