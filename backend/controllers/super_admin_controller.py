from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from utils.decorators import admin_or_programmer_required
from ..models.database import db
from ..models.school import School
from ..models.user import User
from ..models.user_school import UserSchool
from ..services.school_service import SchoolService
from ..services.user_service import UserService

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@super_admin_bp.route('/dashboard', methods=['GET'])
@login_required
@admin_or_programmer_required
def dashboard():
    all_schools = db.session.query(School).order_by(School.nome).all()
    selected_school_id = request.args.get('school_id', type=int)
    
    selected_school = None
    admin_escola_users = []
    alunos = []
    instrutores = []

    if selected_school_id:
        selected_school = db.session.get(School, selected_school_id)
        if selected_school:
            # Buscar admin_escola
            admin_escola_users = db.session.query(User).join(UserSchool).
                filter(UserSchool.school_id == selected_school.id, UserSchool.role == 'admin_escola').all()
            
            # Buscar alunos
            alunos = db.session.query(User).join(UserSchool).
                filter(UserSchool.school_id == selected_school.id, UserSchool.role == 'aluno').all()
            
            # Buscar instrutores
            instrutores = db.session.query(User).join(UserSchool).
                filter(UserSchool.school_id == selected_school.id, UserSchool.role == 'instrutor').all()

    return render_template(
        'super_admin/dashboard.html',
        all_schools=all_schools,
        selected_school=selected_school,
        admin_escola_users=admin_escola_users,
        alunos=alunos,
        instrutores=instrutores
    )

@super_admin_bp.route('/schools', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def manage_schools():
    if request.method == 'POST':
        name = request.form.get('school_name')
        success, message = SchoolService.create_school(name)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('super_admin.manage_schools'))

    schools = db.session.query(School).order_by(School.nome).all()
    return render_template('super_admin/manage_schools.html', schools=schools)

@super_admin_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def manage_assignments():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        school_id = request.form.get('school_id')

        if action == 'assign':
            role = request.form.get('role', 'admin_escola')
            success, message = UserService.assign_school_role(user_id, school_id, role)
        elif action == 'remove':
            success, message = UserService.remove_school_role(user_id, school_id)
        else:
            success, message = False, "Ação inválida."

        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('super_admin.manage_assignments'))

    # GET request logic
    users = db.session.query(User).filter(User.role != 'programador').order_by(User.nome_completo).all()
    schools = db.session.query(School).order_by(School.nome).all()
    assignments = db.session.query(UserSchool).join(User).join(School).all()

    return render_template('super_admin/manage_assignments.html', users=users, schools=schools, assignments=assignments)
