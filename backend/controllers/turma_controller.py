from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from ..services.turma_service import TurmaService, CARGOS_LISTA
from ..forms import TurmaForm, CargosTurmaForm
from utils.decorators import admin_or_programmer_required

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

@turma_bp.route('/')
@login_required
def listar_turmas():
    turmas = TurmaService.get_all_turmas()
    return render_template('listar_turmas.html', turmas=turmas)

@turma_bp.route('/<int:turma_id>')
@login_required
def detalhes_turma(turma_id):
    turma = TurmaService.get_turma_by_id(turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
    
    cargos_atuais = TurmaService.get_cargos_by_turma(turma_id)

    return render_template(
        'detalhes_turma.html', 
        turma=turma,
        cargos_lista=CARGOS_LISTA,
        cargos_atuais=cargos_atuais
    )

@turma_bp.route('/<int:turma_id>/salvar-cargos', methods=['POST'])
@login_required
@admin_or_programmer_required
def salvar_cargos_turma(turma_id):
    turma = TurmaService.get_turma_by_id(turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    form = CargosTurmaForm()
    # Dynamically add fields to the form
    for cargo in CARGOS_LISTA:
        setattr(form, f'cargo_{cargo}', SelectField(cargo, coerce=int))
        field = getattr(form, f'cargo_{cargo}')
        field.choices = [(a.id, a.user.nome_completo) for a in turma.alunos] + [(0, 'Ninguém')]

    if form.validate_on_submit():
        success, message = TurmaService.save_cargos_turma(turma_id, form)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')

    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastrar_turma():
    form = TurmaForm()
    alunos_sem_turma = TurmaService.get_alunos_sem_turma()
    form.alunos_ids.choices = [(a.id, a.user.nome_completo) for a in alunos_sem_turma]

    if form.validate_on_submit():
        success, message = TurmaService.create_turma(form)
        if success:
            flash(message, 'success')
            return redirect(url_for('turma.listar_turmas'))
        else:
            flash(message, 'danger')

    return render_template('cadastrar_turma.html', form=form, alunos_sem_turma=alunos_sem_turma)