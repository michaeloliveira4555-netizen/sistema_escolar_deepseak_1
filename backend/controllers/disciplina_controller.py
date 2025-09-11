from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from ..services.disciplina_service import DisciplinaService
from ..forms import DisciplinaForm, EditDisciplinaForm
from utils.decorators import admin_or_programmer_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

@disciplina_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def adicionar_disciplina():
    form = DisciplinaForm()
    if form.validate_on_submit():
        success, message = DisciplinaService.save_disciplina(form)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'danger')
    
    return render_template('adicionar_disciplina.html', form=form)

@disciplina_bp.route('/listar')
@login_required
def listar_disciplinas():
    pelotao_filtrado = request.args.get('pelotao')
    disciplinas_com_instrutores = DisciplinaService.get_disciplinas_com_instrutores(pelotao_filtrado)
    return render_template(
        'listar_disciplinas.html', 
        disciplinas_com_instrutores=disciplinas_com_instrutores, 
        pelotao_filtrado=pelotao_filtrado
    )

@disciplina_bp.route('/editar/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_disciplina(disciplina_id):
    disciplina = DisciplinaService.get_disciplina_by_id(disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    form = EditDisciplinaForm(obj=disciplina)
    if form.validate_on_submit():
        success, message = DisciplinaService.update_disciplina_com_instrutores(disciplina_id, form)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'danger')

    instrutores = DisciplinaService.get_all_instrutores()
    atribuicoes = DisciplinaService.get_atribuicoes_by_disciplina(disciplina_id)
    disciplinas_com_dois_instrutores = ["AMT I", "AMT II", "Atendimento Pré-Hospitalar Tático"]
    
    return render_template(
        'editar_disciplina.html', 
        form=form,
        disciplina=disciplina, 
        instrutores=instrutores,
        atribuicoes=atribuicoes,
        disciplinas_com_dois_instrutores=disciplinas_com_dois_instrutores
    )