from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..app import db
# IMPORTAÇÃO DO NOVO DECORADOR
from utils.decorators import aluno_profile_required, admin_or_programmer_required
from ..services.user_service import UserService

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
@admin_or_programmer_required
def pre_cadastro():
    role_arg = request.args.get('role')

    if request.method == 'POST':
        # Constrói um dicionário mutável a partir do form
        form_data = request.form.to_dict()
        # Injeta a role da querystring caso não tenha vindo no form (quando chamada por contexto)
        if role_arg and not form_data.get('role'):
            form_data['role'] = role_arg

        id_func_raw = form_data.get('id_func', '').strip()
        # Suporte a múltiplas IDs separadas por '/'
        if '/' in id_func_raw:
            partes = [p.strip() for p in id_func_raw.split('/') if p.strip()]
            ids_numericos = [p for p in partes if p.isdigit()]

            if not form_data.get('role'):
                flash('Função não informada para pré-cadastro em lote.', 'danger')
                return redirect(url_for('main.pre_cadastro', role=role_arg) if role_arg else url_for('main.pre_cadastro'))

            success, novos, existentes = UserService.batch_pre_register_users(ids_numericos, form_data['role'])
            if success:
                flash(f'Pré-cadastro realizado: {novos} novo(s), {existentes} já existente(s).', 'success')
            else:
                flash('Falha ao pré-cadastrar usuários em lote.', 'danger')
            return redirect(url_for('main.pre_cadastro', role=role_arg) if role_arg else url_for('main.pre_cadastro'))
        else:
            success, message = UserService.pre_register_user(form_data)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
            return redirect(url_for('main.pre_cadastro', role=role_arg) if role_arg else url_for('main.pre_cadastro'))

    # GET: passa role_predefinido para o template para controlar a UI
    return render_template('pre_cadastro.html', role_predefinido=role_arg)