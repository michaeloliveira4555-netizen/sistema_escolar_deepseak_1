from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..app import db # CORREÇÃO: Adicionada a importação do objeto db
from ..services.disciplina_service import DisciplinaService
from ..services.instrutor_service import InstrutorService
from utils.decorators import admin_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

@disciplina_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
@admin_required
def cadastro_disciplina():
    instrutores = InstrutorService.get_all_instrutores()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        success, message = DisciplinaService.save_disciplina(form_data)

        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'error')
            return render_template('cadastro_disciplina.html', instrutores=instrutores, form_data=request.form)

    return render_template('cadastro_disciplina.html', instrutores=instrutores, form_data={})

@disciplina_bp.route('/listar')
@login_required
@admin_required
def listar_disciplinas():
    disciplinas = DisciplinaService.get_all_disciplinas()
    return render_template('listar_disciplinas.html', disciplinas=disciplinas)

@disciplina_bp.route('/editar/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_disciplina(disciplina_id):
    disciplina = DisciplinaService.get_disciplina_by_id(disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    instrutores = InstrutorService.get_all_instrutores() # Para o seletor de instrutores

    if request.method == 'POST':
        form_data = request.form.to_dict()
        disciplina_id = request.form.get('disciplina_id')
        
        success, message = DisciplinaService.update_disciplina(disciplina_id, form_data)
        if success:
            if disciplina_id and disciplina_id.isdigit():
                DisciplinaService.update_disciplina_instrutor(int(disciplina_id), disciplina.instrutor_id)
            else:
                DisciplinaService.remove_instrutor_from_disciplina(disciplina.instrutor_id)

            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'error')
            return render_template('editar_disciplina.html', disciplina=disciplina, instrutores=instrutores, form_data=request.form)
            
    return render_template('editar_disciplina.html', disciplina=disciplina, instrutores=instrutores, form_data={})
