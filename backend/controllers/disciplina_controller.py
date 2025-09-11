from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select

from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.horario import Horario
from ..models.historico_disciplina import HistoricoDisciplina
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

@disciplina_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def adicionar_disciplina():
    if request.method == 'POST':
        success, message = DisciplinaService.save_disciplina(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'danger')
            return render_template('adicionar_disciplina.html', form_data=request.form)
    
    return render_template('adicionar_disciplina.html')

@disciplina_bp.route('/listar')
@login_required
def listar_disciplinas():
    pelotao_filtrado = request.args.get('pelotao')
    disciplinas = DisciplinaService.get_all_disciplinas_com_associacoes(pelotao_filtrado)
    disciplinas_com_instrutores = []
    if pelotao_filtrado:
        for disciplina in disciplinas:
            associacao = next((a for a in disciplina.associacoes_turmas if a.pelotao == pelotao_filtrado), None)
            disciplinas_com_instrutores.append((disciplina, associacao))
    else:
        for disciplina in disciplinas:
            disciplinas_com_instrutores.append((disciplina, None))
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
    
    if request.method == 'POST':
        success, message = DisciplinaService.update_disciplina(disciplina_id, request.form.to_dict())
        if success:
            try:
                db.session.commit()
                flash(message, 'success')
                return redirect(url_for('disciplina.listar_disciplinas'))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar as alterações: {e}", 'danger')
        else:
            flash(message, 'danger')
    
    # For GET requests, pass the model object directly
    return render_template('editar_disciplina.html', disciplina=disciplina)

@disciplina_bp.route('/excluir/<int:disciplina_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_disciplina(disciplina_id):
    success, message = DisciplinaService.delete_disciplina(disciplina_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('disciplina.listar_disciplinas'))