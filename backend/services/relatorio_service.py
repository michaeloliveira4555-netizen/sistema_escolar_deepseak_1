from ..models.database import db
from ..models.horario import Horario
from ..models.semana import Semana
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from sqlalchemy import select, func, and_
from collections import defaultdict

class RelatorioService:
    @staticmethod
    def get_horas_aula_por_instrutor(data_inicio, data_fim):
        """
        Busca e totaliza as horas-aula por instrutor e disciplina
        dentro de um período específico.
        """
        # Encontra as semanas que se sobrepõem com o período
        semanas_no_periodo = db.session.scalars(
            select(Semana.id).where(
                and_(
                    Semana.data_inicio <= data_fim,
                    Semana.data_fim >= data_inicio
                )
            )
        ).all()

        if not semanas_no_periodo:
            return []

        # Busca as aulas confirmadas nas semanas encontradas
        aulas = db.session.execute(
            select(
                Horario.instrutor_id,
                Horario.disciplina_id,
                func.sum(Horario.duracao).label('total_horas')
            ).where(
                Horario.semana_id.in_(semanas_no_periodo),
                Horario.status == 'confirmado'
            ).group_by(
                Horario.instrutor_id,
                Horario.disciplina_id
            )
        ).all()

        # Estrutura para agrupar dados por instrutor
        instrutores_dados = defaultdict(lambda: {
            'info': None,
            'disciplinas': [],
            'total_geral': 0
        })

        for aula in aulas:
            instrutor_id = aula.instrutor_id
            instrutor = db.session.get(Instrutor, instrutor_id)

            if instrutor:
                instrutores_dados[instrutor_id]['info'] = instrutor
                
                disciplina = db.session.get(Disciplina, aula.disciplina_id)
                
                disciplina_info = {
                    'nome': disciplina.materia if disciplina else "Disciplina não encontrada",
                    'horas': aula.total_horas
                }
                
                instrutores_dados[instrutor_id]['disciplinas'].append(disciplina_info)
                instrutores_dados[instrutor_id]['total_geral'] += aula.total_horas
        
        # Converte o dicionário para uma lista ordenada por nome do instrutor
        resultado_final = sorted(instrutores_dados.values(), key=lambda x: x['info'].user.nome_completo or "")
        
        return resultado_final