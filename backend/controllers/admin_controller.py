from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from backend.models.database import db
from backend.models.user import User
from utils.decorators import admin_or_programmer_required
from ..services.user_service import UserService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def pre_cadastro():
    if request.method == 'POST':
        id_funcs_raw = request.form.get('id_funcs')
        role = request.form.get('role')

        if not id_funcs_raw or not role:
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('admin.pre_cadastro'))

        id_funcs = [m.strip() for m in id_funcs_raw.replace(',', ' ').replace(';', ' ').split() if m.strip()]
        
        success, new_users_count, existing_users_count = UserService.batch_pre_register_users(id_funcs, role)
        
        if success:
            if new_users_count > 0:
                flash(f'{new_users_count} novo(s) usuário(s) pré-cadastrado(s) com sucesso!', 'success')
            
            if existing_users_count > 0:
                flash(f'{existing_users_count} identificador(es) já existia(m) e foram ignorado(s).', 'info')
        else:
            flash(f'Erro ao pré-cadastrar usuários: {new_users_count}', 'danger')

        return redirect(url_for('admin.pre_cadastro'))

    return render_template('admin/pre_cadastro.html')