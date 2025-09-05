from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

# Mantemos a importação original, pois o app.py já o configura
from ..models.database import db 
from ..services.disciplina_service import DisciplinaService
from ..services.instrutor_service import InstrutorService
# Alteramos o decorator importado para o que permite ambos os perfis
from utils.decorators import admin_or_programmer_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

@disciplina_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required # <-- ALTERADO
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
@admin_or_programmer_required # <-- ALTERADO
def listar_disciplinas():
    disciplinas = DisciplinaService.get_all_disciplinas()
    return render_template('listar_disciplinas.html', disciplinas=disciplinas)

@disciplina_bp.route('/editar/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required # <-- ALTERADO
def editar_disciplina(disciplina_id):
    disciplina = DisciplinaService.get_disciplina_by_id(disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    instrutores = InstrutorService.get_all_instrutores()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # A lógica original aqui parecia um pouco confusa. Simplifiquei para apenas chamar o update.
        success, message = DisciplinaService.update_disciplina(disciplina_id, form_data)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'error')
            # Retorna os dados do formulário para que o usuário não precise preencher tudo de novo
            return render_template('editar_disciplina.html', disciplina=disciplina, instrutores=instrutores, form_data=request.form)
            
    # Na requisição GET, passa o objeto disciplina para o formulário
    return render_template('editar_disciplina.html', disciplina=disciplina, instrutores=instrutores, form_data=disciplina)