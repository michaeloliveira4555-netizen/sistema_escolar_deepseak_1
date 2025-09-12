from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import date
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired

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

# Forms
class AprovarHorarioForm(FlaskForm):
    horario_id = HiddenField('Horário ID', validators=[DataRequired()])
    action = HiddenField('Ação', validators=[DataRequired()]) # 'aprovar' ou 'rejeitar'
    submit = SubmitField('Enviar')

@horario_bp.route('/')
@login_required
def index():
    if current_user.role == 'instrutor':
        if not current_user.instrutor_profile:
            flash('Perfil de instrutor não configurado.', 'warning')
            return redirect(url_for('main.dashboard'))

        vinculos = DisciplinaTurma.query.filter_by(instrutor_id_1=current_user.instrutor_profile.id).all()
        if not vinculos:
            flash('Você não está vinculado a nenhuma turma ou disciplina.', 'warning')
            return redirect(url_for('main.dashboard'))

        turmas_instrutor = list(set([v.pelotao for v in vinculos]))
        if len(turmas_instrutor) == 1:
            semana_id = request.args.get('semana_id')
            return redirect(url_for('horario.index_com_turma', pelotao=turmas_instrutor[0], semana_id=semana_id))

    todas_as_turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    todas_as_semanas = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()

    if not todas_as_turmas or not todas_as_semanas:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=None,
                               semana_selecionada=None,
                               todas_as_turmas=todas_as_turmas,
                               todas_as_semanas=todas_as_semanas)

    turma_selecionada_nome = request.args.get('pelotao', session.get('ultima_turma_visualizada', todas_as_turmas[0].nome))

    semana_id_selecionada = request.args.get('semana_id')
    semana_selecionada = None
    if semana_id_selecionada:
        semana_selecionada = db.session.get(Semana, int(semana_id_selecionada))

    if not semana_selecionada:
        today = date.today()
        semana_selecionada = db.session.scalars(
            select(Semana).where(Semana.data_inicio <= today, Semana.data_fim >= today)
        ).first()
        if not semana_selecionada and todas_as_semanas:
            semana_selecionada = todas_as_semanas[0]

    if not semana_selecionada:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=turma_selecionada_nome,
                               semana_selecionada=None,
                               todas_as_turmas=todas_as_turmas,
                               todas_as_semanas=todas_as_semanas)


    session['ultima_turma_visualizada'] = turma_selecionada_nome

    horario_matrix = HorarioService.construir_matriz_horario(turma_selecionada_nome, semana_selecionada.id)

    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=turma_selecionada_nome,
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=todas_as_turmas,
                           todas_as_semanas=todas_as_semanas)

@horario_bp.route('/<pelotao>')
@login_required
def index_com_turma(pelotao):
    todas_as_semanas = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()

    semana_id_selecionada = request.args.get('semana_id')
    if semana_id_selecionada and semana_id_selecionada != 'None':
        semana_selecionada = db.session.get(Semana, int(semana_id_selecionada))
    else:
        today = date.today()
        semana_selecionada = db.session.scalars(
            select(Semana).where(Semana.data_inicio <= today, Semana.data_fim >= today)
        ).first()
        if not semana_selecionada and todas_as_semanas:
            semana_selecionada = todas_as_semanas[0]

    if not semana_selecionada:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=pelotao,
                               semana_selecionada=None,
                               todas_as_turmas=[db.session.query(Turma).filter_by(nome=pelotao).first()],
                               todas_as_semanas=todas_as_semanas)

    horario_matrix = HorarioService.construir_matriz_horario(pelotao, semana_selecionada.id)
    turma_atual = db.session.query(Turma).filter_by(nome=pelotao).first()

    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=pelotao,
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=[turma_atual] if turma_atual else [],
                           todas_as_semanas=todas_as_semanas)

@horario_bp.route('/editar/<pelotao>/<int:semana_id>')
@login_required
def editar_horario_grid(pelotao, semana_id):
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana não encontrada.", "danger")
        return redirect(url_for('horario.index'))

    is_admin = current_user.role in ['admin', 'programador']
    instrutor_id = current_user.instrutor_profile.id if hasattr(current_user, 'instrutor_profile') and current_user.instrutor_profile else None

    if not is_admin and not instrutor_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('horario.index'))

    horario_matrix = HorarioService.construir_matriz_horario(pelotao, semana_id)

    disciplinas_disponiveis = []
    todos_instrutores = []

    if is_admin:
        todas_disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()
        todos_instrutores_query = db.session.scalars(select(Instrutor).options(joinedload(Instrutor.user)).order_by(Instrutor.id)).all()

        for inst in todos_instrutores_query:
            nome = "Sem nome"
            if inst.user:
                nome = inst.user.nome_completo or inst.user.username or f"User {inst.user.id}"
            todos_instrutores.append({"id": inst.id, "nome": nome})

        for disciplina in todas_disciplinas:
            total_previsto = disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(disciplina_id=disciplina.id, pelotao=pelotao, status='confirmado').scalar() or 0
            disciplinas_disponiveis.append({
                "id": disciplina.id,
                "nome": disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas)
            })
    else:
        associacoes_query = (
            select(DisciplinaTurma).options(joinedload(DisciplinaTurma.disciplina))
            .where(DisciplinaTurma.pelotao == pelotao, (DisciplinaTurma.instrutor_id_1 == instrutor_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_id))
            .order_by(DisciplinaTurma.disciplina_id)
        )
        associacoes = db.session.scalars(associacoes_query).unique().all()
        for a in associacoes:
            total_previsto = a.disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(disciplina_id=a.disciplina.id, pelotao=pelotao, status='confirmado').scalar() or 0
            disciplinas_disponiveis.append({
                "id": a.disciplina.id,
                "nome": a.disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas),
                "instrutor_automatico": instrutor_id
            })

    return render_template(
        'editar_quadro_horario.html',
        horario_matrix=horario_matrix,
        pelotao_selecionado=pelotao,
        semana_selecionada=semana,
        disciplinas_disponiveis=disciplinas_disponiveis,
        todos_instrutores=todos_instrutores,
        is_admin=is_admin,
        instrutor_logado_id=instrutor_id
    )

@horario_bp.route('/get-aula/<int:horario_id>')
@login_required
def get_aula_details(horario_id):
    if not HorarioService.can_edit_horario(horario_id):
        return jsonify({'success': False, 'message': 'Acesso negado. Você não pode editar esta aula.'}), 403
    aula = db.session.get(Horario, horario_id)
    if not aula:
        return jsonify({'success': False, 'message': 'Aula não encontrada'}), 404
    return jsonify({'success': True, 'disciplina_id': aula.disciplina_id, 'instrutor_id': aula.instrutor_id, 'duracao': aula.duracao})

@horario_bp.route('/salvar-aula', methods=['POST'])
@login_required
def salvar_aula():
    data = request.json
    success, message = HorarioService.save_aula(data)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@horario_bp.route('/remover-aula', methods=['POST'])
@login_required
def remover_aula():
    data = request.json
    horario_id = data.get('horario_id')
    success, message = HorarioService.remove_aula(horario_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 403

@horario_bp.route('/aprovar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def aprovar_horarios():
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
    
    aulas_pendentes = db.session.scalars(select(Horario).where(Horario.status == 'pendente').order_by(Horario.id)).all()
    return render_template('aprovar_horarios.html', aulas_pendentes=aulas_pendentes, form=form)