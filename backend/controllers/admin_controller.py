# backend/controllers/admin_controller.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from backend.models.database import db # <-- Importação correta para sua estrutura
from backend.models.user import User

# Blueprint para rotas de administração
admin_bp = Blueprint('admin', __name__)

# Decorator para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Você precisa ser um administrador.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
@admin_required
def pre_cadastro():
    if request.method == 'POST':
        matriculas_raw = request.form.get('matriculas')
        role = request.form.get('role')

        if not matriculas_raw or not role:
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('admin.pre_cadastro'))

        matriculas = [m.strip() for m in matriculas_raw.replace(',', ' ').replace(';', ' ').split() if m.strip()]
        
        novos_usuarios = 0
        usuarios_existentes = 0
        
        for matricula in matriculas:
            user_exists = db.session.execute(
                db.select(User).filter_by(matricula=matricula, role=role)
            ).scalar_one_or_none()

            if user_exists:
                usuarios_existentes += 1
            else:
                new_user = User(matricula=matricula, role=role, is_active=False)
                db.session.add(new_user)
                novos_usuarios += 1
        
        if novos_usuarios > 0:
            db.session.commit()
            flash(f'{novos_usuarios} novo(s) usuário(s) pré-cadastrado(s) com sucesso!', 'success')
        
        if usuarios_existentes > 0:
            flash(f'{usuarios_existentes} identificador(es) já existia(m) e foram ignorado(s).', 'info')

        return redirect(url_for('admin.pre_cadastro'))

    return render_template('admin/pre_cadastro.html')