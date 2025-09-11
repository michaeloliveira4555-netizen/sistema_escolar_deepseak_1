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
    def get_horas_aula_por_instrutor(data_inicio, data_fim):
        """
        Busca e totaliza as horas-aula por instrutor e disciplina
        dentro de um período específico.
        """
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
            'disciplinas': [],
            'total_geral': 0
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