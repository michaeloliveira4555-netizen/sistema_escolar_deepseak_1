from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..models.school import School
from ..models.database import db
from ..services.dashboard_service import DashboardService
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
    viewing_school = None
    school_id_to_load = None

    # 1. Verifica se o Super Admin está no modo "Visualizar como"
    view_as_school_id = request.args.get('view_as_school', type=int)
    if current_user.role in ['super_admin', 'programador'] and view_as_school_id:
        school_id_to_load = view_as_school_id
        viewing_school = db.session.get(School, school_id_to_load)
        if not viewing_school:
            flash("Escola selecionada para visualização não encontrada.", "danger")
            return redirect(url_for('super_admin.dashboard'))
    else:
        # 2. Para usuários normais, encontra a primeira escola associada
        if current_user.schools:
            school_id_to_load = current_user.schools[0].id
        else:
            # Se o usuário não tem escola (ex: super_admin sem modo de visualização),
            # school_id_to_load permanece None, mostrando dados globais.
            pass

    dashboard_data = DashboardService.get_dashboard_data(school_id=school_id_to_load)
    
    # Define qual escola está em contexto para exibição no template
    school_in_context = viewing_school or (current_user.schools[0] if current_user.schools else None)

    return render_template('dashboard.html', 
                           dashboard_data=dashboard_data, 
                           viewing_school=viewing_school,
                           school_in_context=school_in_context)

@main_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def pre_cadastro():
    role_arg = request.args.get('role')

    if request.method == 'POST':
        form_data = request.form.to_dict()
        if role_arg and not form_data.get('role'):
            form_data['role'] = role_arg

        id_func_raw = form_data.get('id_func', '').strip()
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

    return render_template('pre_cadastro.html', role_predefinido=role_arg)