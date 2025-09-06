from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    dashboard_data = {} 
    return render_template('dashboard.html', dashboard_data=dashboard_data)

@main_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
def pre_cadastro():
    # Garante que apenas administradores possam acessar
    if current_user.role not in ['admin', 'programador']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        id_func = request.form.get('id_func', '').strip()
        role = request.form.get('role')

        if not id_func or not role:
            flash('Por favor, preencha todos os campos.', 'warning')
            return render_template('pre_cadastro.html')
        
        if not id_func.isdigit():
            flash('A Identidade Funcional deve conter apenas números.', 'danger')
            return render_template('pre_cadastro.html')

        # Verifica se um usuário com esta Id Func já existe
        user_exists = db.session.execute(db.select(User).filter_by(id_func=id_func)).scalar_one_or_none()
        
        if user_exists:
            flash(f'A Id Func "{id_func}" já está pré-cadastrada no sistema.', 'danger')
        else:
            new_user = User(
                id_func=id_func,
                role=role,
                is_active=False # O usuário é criado como inativo
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'Usuário com Id Func "{id_func}" pré-cadastrado com sucesso!', 'success')
        
        return redirect(url_for('main.pre_cadastro'))

    return render_template('pre_cadastro.html')