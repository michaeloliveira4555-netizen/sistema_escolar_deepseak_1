# backend/controllers/super_admin_controller.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required
import secrets
import string
from utils.decorators import super_admin_or_programmer_required
from ..models.database import db
from ..models.school import School
from ..models.user import User
from ..models.user_school import UserSchool
from ..services.school_service import SchoolService
from ..services.user_service import UserService

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@super_admin_bp.route('/dashboard', methods=['GET'])
@login_required
@super_admin_or_programmer_required
def dashboard():
    all_schools = db.session.query(School).order_by(School.nome).all()
    # ... (resto da função)
    return render_template('super_admin/dashboard.html', all_schools=all_schools)

@super_admin_bp.route('/exit-view')
@login_required
@super_admin_or_programmer_required
def exit_view():
    session.pop('view_as_school_id', None)
    session.pop('view_as_school_name', None)
    flash('Você saiu do modo de visualização.', 'info')
    return redirect(url_for('super_admin.dashboard'))

@super_admin_bp.route('/schools', methods=['GET', 'POST'])
@login_required
@super_admin_or_programmer_required
def manage_schools():
    if request.method == 'POST':
        # ... (lógica do POST)
        pass
    schools = db.session.query(School).order_by(School.nome).all()
    return render_template('super_admin/manage_schools.html', schools=schools)

@super_admin_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@super_admin_or_programmer_required
def manage_assignments():
    # ... (lógica da função)
    users = db.session.query(User).filter(User.role != 'programador').order_by(User.nome_completo).all()
    schools = db.session.query(School).order_by(School.nome).all()
    assignments = db.session.query(UserSchool).join(User).join(School).all()
    return render_template('super_admin/manage_assignments.html', users=users, schools=schools, assignments=assignments)

@super_admin_bp.route('/create-administrator', methods=['POST'])
@login_required
@super_admin_or_programmer_required
def create_administrator():
    # ... (lógica da função)
    pass
    nome_completo = request.form.get('nome_completo')
    email = request.form.get('email')
    id_func = request.form.get('id_func')
    school_id = request.form.get('school_id')

    if not all([nome_completo, email, id_func, school_id]):
        flash('Todos os campos são obrigatórios.', 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    existing_user = User.query.filter((User.email == email) | (User.id_func == id_func)).first()
    if existing_user:
        flash('Um usuário com este email ou ID Funcional já existe.', 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(10))

    new_user = User(
        nome_completo=nome_completo,
        email=email,
        id_func=id_func,
        role='admin_escola',
        is_active=True,
        must_change_password=True
    )
    new_user.set_password(temp_password)
    
    db.session.add(new_user)
    db.session.flush()

    user_school = UserSchool(
        user_id=new_user.id,
        school_id=school_id,
        role='admin_escola'
    )
    db.session.add(user_school)
    
    try:
        db.session.commit()
        flash(f'Administrador "{nome_completo}" criado com sucesso! Senha temporária: {temp_password}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar administrador: {e}', 'danger')

    return redirect(url_for('super_admin.manage_schools'))

@super_admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@super_admin_or_programmer_required
def delete_user(user_id):
    success, message = UserService.delete_user_by_id(user_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('super_admin.manage_assignments'))