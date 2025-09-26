# backend/controllers/super_admin_controller.py

from __future__ import annotations

from typing import Optional

import secrets
import string
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required

from utils.decorators import super_admin_or_programmer_required
from ..models.database import db
from ..models.school import School
from ..models.user import User
from ..models.user_school import UserSchool
from ..services.school_service import SchoolService
from ..services.user_service import UserService


super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')


def _as_int(value: object) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@super_admin_bp.route('/dashboard', methods=['GET'])
@login_required
@super_admin_or_programmer_required
def dashboard():
    all_schools = db.session.query(School).order_by(School.nome).all()
    return render_template('super_admin/dashboard.html', all_schools=all_schools)


@super_admin_bp.route('/exit-view')
@login_required
@super_admin_or_programmer_required
def exit_view():
    session.pop('view_as_school_id', None)
    session.pop('view_as_school_name', None)
    flash('Voce saiu do modo de visualizacao.', 'info')
    return redirect(url_for('super_admin.dashboard'))


@super_admin_bp.route('/schools', methods=['GET', 'POST'])
@login_required
@super_admin_or_programmer_required
def manage_schools():
    if request.method == 'POST':
        school_name = (request.form.get('school_name') or '').strip()
        if not school_name:
            flash('Informe o nome da escola.', 'danger')
        else:
            success, message = SchoolService.create_school(school_name)
            flash(message, 'success' if success else 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    schools = db.session.query(School).order_by(School.nome).all()
    return render_template('super_admin/manage_schools.html', schools=schools)


@super_admin_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@super_admin_or_programmer_required
def manage_assignments():
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip()
        user_id = _as_int(request.form.get('user_id'))
        school_id = _as_int(request.form.get('school_id'))

        if action == 'assign':
            role = (request.form.get('role') or '').strip()
            if not all([user_id, school_id, role]):
                flash('Informe usuario, escola e papel para criar o vinculo.', 'danger')
            else:
                success, message = UserService.assign_school_role(user_id, school_id, role)
                flash(message, 'success' if success else 'danger')
        elif action == 'remove':
            if not user_id or not school_id:
                flash('Dados insuficientes para remover o vinculo.', 'danger')
            else:
                success, message = UserService.remove_school_role(user_id, school_id)
                flash(message, 'success' if success else 'danger')
        else:
            flash('Acao desconhecida ao gerenciar vinculos.', 'warning')

        return redirect(url_for('super_admin.manage_assignments'))

    users = (
        db.session.query(User)
        .filter(User.role != 'programador')
        .order_by(User.nome_completo, User.id_func)
        .all()
    )
    schools = db.session.query(School).order_by(School.nome).all()
    assignments = (
        db.session.query(UserSchool)
        .join(User)
        .join(School)
        .order_by(School.nome, User.nome_completo, User.id_func)
        .all()
    )
    return render_template(
        'super_admin/manage_assignments.html',
        users=users,
        schools=schools,
        assignments=assignments,
    )


@super_admin_bp.route('/create-administrator', methods=['POST'])
@login_required
@super_admin_or_programmer_required
def create_administrator():
    nome_completo = (request.form.get('nome_completo') or '').strip()
    email = (request.form.get('email') or '').strip()
    id_func = (request.form.get('id_func') or '').strip()
    school_id = _as_int(request.form.get('school_id'))

    if not all([nome_completo, email, id_func, school_id]):
        flash('Todos os campos sao obrigatorios.', 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    existing_user = User.query.filter((User.email == email) | (User.id_func == id_func)).first()
    if existing_user:
        flash('Ja existe usuario com este email ou ID funcional.', 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

    new_user = User(
        nome_completo=nome_completo,
        email=email,
        id_func=id_func,
        role='admin_escola',
        is_active=True,
        must_change_password=True,
    )
    new_user.set_password(temp_password)
    db.session.add(new_user)

    try:
        db.session.flush()
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao preparar cadastro do administrador: {exc}', 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    success, message = UserService.assign_school_role(new_user.id, school_id, 'admin_escola')
    if success:
        flash(
            f'Administrador "{nome_completo}" criado com sucesso. Senha temporaria: {temp_password}',
            'success',
        )
    else:
        db.session.rollback()
        flash(f'Falha ao vincular administrador a escola: {message}', 'danger')

    return redirect(url_for('super_admin.manage_schools'))


@super_admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@super_admin_or_programmer_required
def delete_user(user_id):
    success, message = UserService.delete_user_by_id(user_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('super_admin.manage_assignments'))
