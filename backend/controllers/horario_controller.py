# backend/controllers/horario_controller.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import date, timedelta # Adicionado timedelta
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired

# Imports dos Models e Services
from ..models.database import db
from ..models.horario import Horario
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.semana import Semana
from ..models.turma import Turma
from utils.decorators import admin_or_programmer_required
from ..services.horario_service import HorarioService

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

# --- Formulários ---
class AprovarHorarioForm(FlaskForm):
    horario_id = HiddenField('Horário ID', validators=[DataRequired()])
    action = HiddenField('Ação', validators=[DataRequired()]) # 'aprovar' ou 'rejeitar'
    submit = SubmitField('Enviar')


# --- Rotas (Views / Controllers) ---

@horario_bp.route('/')
@login_required
def index():
    """
    Página principal do Quadro de Horários.
    Exibe a visão geral com seletores de ciclo, turma e semana.
    """
    ciclo_selecionado = request.args.get('ciclo', session.get('ultimo_ciclo_horario', 1), type=int)
    session['ultimo_ciclo_horario'] = ciclo_selecionado

    # Lógica para determinar quais turmas o usuário pode ver
    if current_user.role == 'instrutor':
        if not current_user.instrutor_profile:
            flash('Perfil de instrutor não configurado.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        nomes_turmas_instrutor = HorarioService.get_turmas_do_instrutor(current_user.instrutor_profile.id)
        
        if not nomes_turmas_instrutor:
            flash('Você não está vinculado a nenhuma turma ou disciplina.', 'warning')
            return redirect(url_for('main.dashboard'))

        todas_as_turmas = db.session.scalars(
            select(Turma).where(Turma.nome.in_(nomes_turmas_instrutor)).order_by(Turma.nome)
        ).all()
    else:
        todas_as_turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()

    # Busca as semanas para o ciclo selecionado
    todas_as_semanas = db.session.scalars(
        select(Semana).where(Semana.ciclo == ciclo_selecionado).order_by(Semana.data_inicio.desc())
    ).all()

    # Determina a turma selecionada
    turma_selecionada_nome = request.args.get('pelotao', session.get('ultima_turma_visualizada'))
    if not turma_selecionada_nome and todas_as_turmas:
        turma_selecionada_nome = todas_as_turmas[0].nome
    session['ultima_turma_visualizada'] = turma_selecionada_nome

    # Determina a semana selecionada
    semana_id = request.args.get('semana_id')
    semana_selecionada = HorarioService.get_semana_selecionada(semana_id, ciclo_selecionado)
    
    # Prepara dados para o template
    horario_matrix = None
    datas_semana = {}
    if turma_selecionada_nome and semana_selecionada:
        horario_matrix = HorarioService.construir_matriz_horario(turma_selecionada_nome, semana_selecionada.id)
        datas_semana = HorarioService.get_datas_da_semana(semana_selecionada)

    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=turma_selecionada_nome,
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=todas_as_turmas,
                           todas_as_semanas=todas_as_semanas,
                           ciclos=[1, 2, 3],
                           ciclo_selecionado=ciclo_selecionado,
                           datas_semana=datas_semana)

@horario_bp.route('/editar/<pelotao>/<int:semana_id>/<int:ciclo_id>')
@login_required
@admin_or_programmer_required
def editar_horario_grid(pelotao, semana_id, ciclo_id):
    """
    Página de edição do Quadro de Horários (visão de grade).
    """
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana não encontrada.", "danger")
        return redirect(url_for('horario.index'))

    # Delega a busca de dados para o Service
    context_data = HorarioService.get_edit_grid_context(pelotao, semana_id, ciclo_id, current_user)
    
    if not context_data['success']:
        flash(context_data['message'], 'danger')
        return redirect(url_for('horario.index'))

    return render_template('editar_quadro_horario.html', **context_data)


@horario_bp.route('/get-aula/<int:horario_id>')
@login_required
def get_aula_details(horario_id):
    """
    API para obter os detalhes de uma aula existente para edição.
    """
    aula = HorarioService.get_aula_details(horario_id, current_user)
    if not aula:
        return jsonify({'success': False, 'message': 'Aula não encontrada ou acesso negado.'}), 404
    
    return jsonify({'success': True, 'data': aula})

@horario_bp.route('/salvar-aula', methods=['POST'])
@login_required
def salvar_aula():
    """
    API para salvar (criar ou atualizar) uma aula no horário.
    A lógica foi movida para o HorarioService.
    """
    data = request.json
    success, message, status_code = HorarioService.save_aula(data, current_user)
    
    return jsonify({'success': success, 'message': message}), status_code

@horario_bp.route('/remover-aula', methods=['POST'])
@login_required
def remover_aula():
    """
    API para remover uma aula do horário.
    """
    data = request.json
    horario_id = data.get('horario_id')
    success, message = HorarioService.remove_aula(horario_id, current_user)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 403

@horario_bp.route('/aprovar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def aprovar_horarios():
    """
    Página para administradores aprovarem ou negarem aulas pendentes.
    """
    form = AprovarHorarioForm()
    if form.validate_on_submit():
        horario_id = form.horario_id.data
        action = form.action.data
        success, message = HorarioService.aprovar_horario(horario_id, action)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('horario.aprovar_horarios'))
        
    aulas_pendentes = HorarioService.get_aulas_pendentes()
    return render_template('aprovar_horarios.html', aulas_pendentes=aulas_pendentes, form=form)