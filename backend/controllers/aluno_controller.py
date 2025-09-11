from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select

from ..models.database import db
from ..services.aluno_service import AlunoService
from ..models.turma import Turma
from ..forms import AlunoProfileForm, AdminCreateAlunoForm, AdminEditAlunoForm, SelfEditAlunoForm
from utils.decorators import admin_or_programmer_required

aluno_bp = Blueprint('aluno', __name__, url_prefix='/aluno')

@aluno_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    form = AlunoProfileForm()
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    form.turma_id.choices = [(t.id, t.nome) for t in turmas]

    if form.validate_on_submit():
        success, message = AlunoService.save_aluno(current_user.id, form)

        if success:
            flash(message, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('cadastro_aluno.html', form=form, turmas=turmas)

@aluno_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_aluno_admin():
    form = AdminCreateAlunoForm()
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    form.turma_id.choices = [(t.id, t.nome) for t in turmas]

    if form.validate_on_submit():
        success, message = AlunoService.create_aluno_with_user(form)
        if success:
            flash(message, 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            flash(message, 'error')

    return render_template('cadastro_aluno_admin.html', form=form, turmas=turmas)

@aluno_bp.route('/listar')
@login_required
def listar_alunos():
    turma_filtrada = request.args.get('turma', None)
    alunos = AlunoService.get_all_alunos(turma_filtrada)
    
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    
    return render_template('listar_alunos.html', alunos=alunos, turmas=turmas, turma_filtrada=turma_filtrada)

@aluno_bp.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def editar_meu_perfil():
    if not current_user.aluno_profile:
        flash('Perfil de aluno não encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    aluno_id = current_user.aluno_profile.id
    aluno = AlunoService.get_aluno_by_id(aluno_id)
    form = SelfEditAlunoForm(obj=aluno)

    if form.validate_on_submit():
        success, message = AlunoService.update_aluno(aluno_id, form, form.foto_perfil.data)
        if success:
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('aluno.editar_meu_perfil'))
        else:
            flash(message, 'error')
            
    return render_template('editar_aluno.html', form=form, aluno=aluno, self_edit=True)

@aluno_bp.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_aluno(aluno_id):
    aluno = AlunoService.get_aluno_by_id(aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('aluno.listar_alunos'))

    if request.method == 'POST':
        form = AdminEditAlunoForm()
    else:
        form = AdminEditAlunoForm(obj=aluno)
        form.nome_completo.data = aluno.user.nome_completo
        form.email.data = aluno.user.email

    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    form.turma_id.choices = [(t.id, t.nome) for t in turmas]

    if form.validate_on_submit():
        success, message = AlunoService.update_aluno(aluno_id, form, form.foto_perfil.data)
        if success:
            flash(message, 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            flash(message, 'error')
    elif request.method == 'POST':
        print("Form validation errors (AdminEditAlunoForm):", form.errors)
        flash("Por favor, corrija os erros no formulário.", 'error')
            
    return render_template('editar_aluno.html', form=form, aluno=aluno, turmas=turmas)