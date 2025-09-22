# backend/controllers/turma_controller.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select, or_
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget

# Imports dos Models e Services
from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.turma_cargo import TurmaCargo
from utils.decorators import admin_or_programmer_required
from ..services.turma_service import TurmaService

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

# Lista de cargos fixa para consistência
CARGOS_LISTA = [
    "Auxiliar do Pelotão", "Chefe de Turma", "C1", "C2", "C3", "C4", "C5"
]

# --- Formulários ---
class TurmaForm(FlaskForm):
    nome = StringField('Nome da Turma', validators=[DataRequired(), Length(max=100)])
    ano = IntegerField('Ano da Turma', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    alunos_ids = SelectMultipleField('Alunos da Turma', coerce=int, validators=[Optional()],
                                     option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False))
    submit = SubmitField('Salvar Turma')

class TurmaCargoForm(FlaskForm):
    submit = SubmitField('Salvar Cargos')

class DeleteForm(FlaskForm):
    pass

# --- Rotas (Views / Controllers) ---

@turma_bp.route('/')
@login_required
def listar_turmas():
    delete_form = DeleteForm()
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas, delete_form=delete_form)

@turma_bp.route('/<int:turma_id>')
@login_required
def detalhes_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
    
    # Busca os cargos e alunos da turma através do service
    cargos_atuais = TurmaService.get_cargos_da_turma(turma_id, CARGOS_LISTA)
    
    form = TurmaCargoForm()
    return render_template(
        'detalhes_turma.html',
        turma=turma,
        cargos_lista=CARGOS_LISTA,
        cargos_atuais=cargos_atuais,
        form=form
    )

@turma_bp.route('/<int:turma_id>/salvar-cargos', methods=['POST'])
@login_required
@admin_or_programmer_required
def salvar_cargos_turma(turma_id):
    form = TurmaCargoForm()
    if form.validate_on_submit():
        success, message = TurmaService.atualizar_cargos(turma_id, request.form)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Falha na validação do formulário.', 'danger')
    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastrar_turma():
    form = TurmaForm()
    # Busca alunos sem turma para popular o formulário
    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(Aluno.turma_id.is_(None))
    ).all()
    form.alunos_ids.choices = [(a.id, a.user.nome_completo) for a in alunos_sem_turma]

    if form.validate_on_submit():
        success, message = TurmaService.create_turma(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('turma.listar_turmas'))
        else:
            flash(message, 'danger')
    
    return render_template('cadastrar_turma.html', form=form, alunos_sem_turma=alunos_sem_turma)

@turma_bp.route('/editar/<int:turma_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
    
    form = TurmaForm(obj=turma)
    # Alunos disponíveis são os que não têm turma ou os que já estão nesta turma
    alunos_disponiveis = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id.is_(None), Aluno.turma_id == turma_id))
    ).all()
    form.alunos_ids.choices = [(a.id, a.user.nome_completo) for a in alunos_disponiveis]
    
    if form.validate_on_submit():
        success, message = TurmaService.update_turma(turma_id, form)
        if success:
            flash(message, 'success')
            return redirect(url_for('turma.listar_turmas'))
        else:
            flash(message, 'danger')

    if request.method == 'GET':
        form.alunos_ids.data = [a.id for a in turma.alunos]

    return render_template('editar_turma.html', form=form, turma=turma, alunos_disponiveis=alunos_disponiveis)


@turma_bp.route('/excluir/<int:turma_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_turma(turma_id):
    form = DeleteForm()
    if form.validate_on_submit():
        success, message = TurmaService.delete_turma(turma_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Falha na validação do token CSRF.', 'danger')
    return redirect(url_for('turma.listar_turmas'))