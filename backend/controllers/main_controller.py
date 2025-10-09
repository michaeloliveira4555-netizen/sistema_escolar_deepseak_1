# backend/controllers/main_controller.py

from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user

from ..models.school import School
from ..models.database import db
from ..services.dashboard_service import DashboardService
from utils.decorators import admin_or_programmer_required
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
    if current_user.role not in ['super_admin', 'programador']:
        session.pop('view_as_school_id', None)
        session.pop('view_as_school_name', None)

    view_as_school_id = request.args.get('view_as_school', type=int)

    if current_user.role in ['super_admin', 'programador'] and view_as_school_id:
        school = db.session.get(School, view_as_school_id)
        if school:
            session['view_as_school_id'] = school.id
            session['view_as_school_name'] = school.nome
        else:
            flash('Escola selecionada para visualizacao nao foi encontrada.', 'danger')
            return redirect(url_for('super_admin.dashboard'))

    school_id_to_load = None
    if current_user.role in ['super_admin', 'programador']:
        school_id_to_load = session.get('view_as_school_id')
    elif current_user.schools:
        school_id_to_load = current_user.schools[0].id

    dashboard_data = DashboardService.get_dashboard_data(school_id=school_id_to_load)

    school_in_context = None
    if school_id_to_load:
        school_in_context = db.session.get(School, school_id_to_load)

    return render_template(
        'dashboard.html',
        dashboard_data=dashboard_data,
        school_in_context=school_in_context,
    )


@main_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def pre_cadastro():
    role_arg = request.args.get('role')
    redirect_target = url_for('main.pre_cadastro', role=role_arg) if role_arg else url_for('main.pre_cadastro')

    if request.method == 'POST':
        form_data = request.form.to_dict()
        if role_arg and not form_data.get('role'):
            form_data['role'] = role_arg

        school_id = form_data.get('school_id')
        if not school_id and current_user.role == 'admin_escola':
            user_school = current_user.user_schools[0] if current_user.user_schools else None
            if not user_school:
                flash('Associe sua conta a uma escola antes de realizar o pre-cadastro.', 'danger')
                return redirect(redirect_target)
            school_id = user_school.school_id

        if not school_id:
            flash('Selecione a escola para concluir o pre-cadastro.', 'danger')
            return redirect(redirect_target)

        form_data['school_id'] = school_id

        id_funcs_raw = (form_data.get('id_funcs') or '').strip()
        if any(sep in id_funcs_raw for sep in ('/', ' ', ',', ';', '\n', '\r')):
            parts = [p.strip() for p in id_funcs_raw.replace(',', ' ').replace(';', ' ').split() if p.strip()]
            ids_numericos = [p for p in parts if p.isdigit()]

            if not form_data.get('role'):
                flash('Informe a funcao para o pre-cadastro em lote.', 'danger')
                return redirect(redirect_target)

            success, novos, existentes = UserService.batch_pre_register_users(ids_numericos, form_data['role'], school_id)
            if success:
                flash(f'Pre-cadastro realizado: {novos} novo(s), {existentes} ja existente(s).', 'success')
            else:
                flash('Falha ao pre-cadastrar usuarios em lote.', 'danger')
            return redirect(redirect_target)
        else:
            form_data['id_func'] = id_funcs_raw
            success, message = UserService.pre_register_user(form_data)
            flash(message, 'success' if success else 'danger')
            return redirect(redirect_target)

    schools = db.session.query(School).order_by(School.nome).all()
    return render_template('pre_cadastro.html', role_predefinido=role_arg, schools=schools)
