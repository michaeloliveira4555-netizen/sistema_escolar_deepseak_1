from ..models.database import db
from ..models.horario import Horario
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.semana import Semana
from ..models.turma import Turma
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from flask_login import current_user
from flask import current_app

class HorarioService:
    @staticmethod
    def can_edit_horario(horario_id):
        """Verifica se o usuário atual pode editar/deletar um horário específico"""
        if current_user.role in ['admin', 'programador']:
            return True

        if current_user.role == 'instrutor' and current_user.instrutor_profile:
            horario = db.session.get(Horario, horario_id)
            if horario and horario.instrutor_id == current_user.instrutor_profile.id:
                return True

        return False

    @staticmethod
    def construir_matriz_horario(pelotao, semana_id):
        a_disposicao = {'materia': 'A disposição do C Al /S Ens', 'instrutor': None, 'duracao': 1, 'is_disposicao': True, 'id': None}
        horario_matrix = [[dict(a_disposicao) for _ in range(7)] for _ in range(15)]
        dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        aulas_agendadas = db.session.scalars(
            select(Horario).options(joinedload(Horario.disciplina), joinedload(Horario.instrutor).joinedload(Instrutor.user))
            .where(Horario.pelotao == pelotao, Horario.semana_id == semana_id)
        ).all()
        for aula in aulas_agendadas:
            try:
                dia_idx = dias.index(aula.dia_semana)
                periodo_idx = aula.periodo - 1
                if 0 <= periodo_idx < 15 and 0 <= dia_idx < 7:
                    instrutor_nome = "N/D"
                    if aula.instrutor and aula.instrutor.user:
                        instrutor_nome = aula.instrutor.user.nome_completo or aula.instrutor.user.username
                    can_edit = HorarioService.can_edit_horario(aula.id)
                    aula_info = {
                        'id': aula.id,
                        'materia': aula.disciplina.materia,
                        'instrutor': instrutor_nome,
                        'duracao': aula.duracao,
                        'status': aula.status,
                        'is_disposicao': False,
                        'can_edit': can_edit,
                    }
                    horario_matrix[periodo_idx][dia_idx] = aula_info
                    for i in range(1, aula.duracao):
                        if periodo_idx + i < 15:
                            horario_matrix[periodo_idx + i][dia_idx] = 'SKIP'
            except (ValueError, IndexError):
                continue
        return horario_matrix

    @staticmethod
    def save_aula(data):
        horario_id = data.get('horario_id')
        is_admin = current_user.role in ['admin', 'programador']

        # --- Input Validation --- #
        pelotao = data.get('pelotao')
        semana_id = data.get('semana_id')
        dia_semana = data.get('dia')
        periodo = data.get('periodo')
        duracao = data.get('duracao', 1)
        disciplina_id = data.get('disciplina_id')

        if not all([pelotao, semana_id, dia_semana, periodo, disciplina_id]):
            return False, 'Todos os campos obrigatórios devem ser preenchidos.'

        try:
            semana_id = int(semana_id)
            periodo = int(periodo)
            duracao = int(duracao)
            disciplina_id = int(disciplina_id)
        except ValueError:
            return False, 'IDs, período e duração devem ser números inteiros válidos.'

        # Validate existence of Pelotao (Turma)
        turma_existe = db.session.scalars(select(Turma).where(Turma.nome == pelotao)).first()
        if not turma_existe:
            return False, 'Pelotão (Turma) não encontrado.'

        # Validate existence of Semana
        semana_existe = db.session.get(Semana, semana_id)
        if not semana_existe:
            return False, 'Semana não encontrada.'

        # Validate Dia da Semana
        dias_validos = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        if dia_semana not in dias_validos:
            return False, 'Dia da semana inválido.'

        # Validate Periodo and Duracao ranges
        if not (1 <= periodo <= 15):
            return False, 'Período deve ser entre 1 e 15.'
        if not (1 <= duracao <= 3): # Assuming max 3 consecutive periods for a single class
            return False, 'Duração deve ser entre 1 e 3.'
        if (periodo + duracao - 1) > 15: # Check if class duration exceeds daily periods
            return False, 'A duração da aula excede o limite de períodos do dia.'

        # End Input Validation #

        if is_admin:
            if not data.get('instrutor_id'):
                return False, 'Instrutor é obrigatório para administradores.'
            try:
                instrutor_final_id = int(data.get('instrutor_id'))
            except ValueError:
                return False, 'ID do instrutor deve ser um número inteiro válido.'
        else:
            if not current_user.instrutor_profile:
                return False, 'Usuário não é um instrutor válido.'
            instrutor_final_id = current_user.instrutor_profile.id

        disciplina = db.session.get(Disciplina, disciplina_id)
        if not disciplina:
            return False, 'Disciplina não encontrada.'

        instrutor = db.session.get(Instrutor, instrutor_final_id)
        if not instrutor:
            return False, 'Instrutor não encontrado.'

        if not is_admin:
            associacao = db.session.execute(
                select(DisciplinaTurma).where(
                    DisciplinaTurma.pelotao == pelotao,
                    DisciplinaTurma.disciplina_id == disciplina_id,
                    (DisciplinaTurma.instrutor_id_1 == instrutor_final_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_final_id)
                )
            ).scalar_one_or_none()
            if not associacao:
                return False, 'Você não está autorizado para esta disciplina neste pelotão.'

        try:
            if horario_id:
                if not HorarioService.can_edit_horario(int(horario_id)):
                    return False, 'Acesso negado. Você não pode editar esta aula.'
                aula = db.session.get(Horario, int(horario_id))
                if not aula:
                    return False, 'Aula não encontrada.'
                aula.disciplina_id = disciplina_id
                aula.instrutor_id = instrutor_final_id
                aula.duracao = duracao
                aula.status = 'confirmado' if is_admin else 'pendente'
            else:
                # Check for conflicts for the entire duration of the new class
                for i in range(duracao):
                    conflito = db.session.execute(
                        select(Horario).where(
                            Horario.pelotao == pelotao,
                            Horario.semana_id == semana_id,
                            Horario.dia_semana == dia_semana,
                            Horario.periodo == (periodo + i)
                        )
                    ).scalar_one_or_none()
                    if conflito:
                        return False, f'Já existe uma aula agendada no período {periodo + i} deste horário.'

                aula = Horario()
                aula.pelotao = pelotao
                aula.semana_id = semana_id
                aula.dia_semana = dia_semana
                aula.periodo = periodo
                aula.disciplina_id = disciplina_id
                aula.instrutor_id = instrutor_final_id
                aula.duracao = duracao
                aula.status = 'confirmado' if is_admin else 'pendente'
                db.session.add(aula)
            db.session.commit()
            return True, 'Aula salva com sucesso!'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar aula: {e}")
            return False, f'Erro interno: {str(e)}'

    @staticmethod
    def remove_aula(horario_id):
        if not HorarioService.can_edit_horario(int(horario_id)):
            return False, 'Acesso negado. Você não pode remover esta aula.'
        try:
            aula = db.session.get(Horario, int(horario_id))
            if aula:
                db.session.delete(aula)
                db.session.commit()
                return True, 'Aula removida com sucesso!'
            return False, 'Aula não encontrada.'
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao remover aula: {e}")
            return False, 'Ocorreu um erro ao remover a aula.'

    @staticmethod
    def aprovar_horario(horario_id, action):
        horario = db.session.get(Horario, int(horario_id))
        if not horario:
            return False, 'Horário não encontrado.'

        try:
            if action == 'aprovar':
                horario.status = 'confirmado'
                message = f'Aula de {horario.disciplina.materia} aprovada com sucesso!'
            elif action == 'negar':
                db.session.delete(horario)
                message = f'Aula de {horario.disciplina.materia} negada e removida com sucesso!'
            else:
                return False, 'Ação inválida.'
            
            db.session.commit()
            return True, message
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao processar horário: {e}")
            return False, 'Ocorreu um erro ao processar o horário.'