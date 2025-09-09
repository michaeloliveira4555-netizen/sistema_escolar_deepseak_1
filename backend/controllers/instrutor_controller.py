from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models.user import User
from ..services.instrutor_service import InstrutorService
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_required
from utils.validators import validate_username, validate_email, validate_password_strength, validate_cpf, validate_telefone

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

@instrutor_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_instrutor():
    instrutor = InstrutorService.get_instrutor_by_id(current_user.id)
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        success, message = InstrutorService.save_instrutor(current_user.id, form_data)

        if success:
            flash(message, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'error')
            return render_template('cadastro_instrutor.html', form_data=form_data, instrutor=instrutor, disciplinas=disciplinas, is_admin_flow=False)

    return render_template('cadastro_instrutor.html', form_data={}, instrutor=instrutor, disciplinas=disciplinas, is_admin_flow=False)

@instrutor_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_required
def cadastro_instrutor_admin():
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = 'instrutor'

        matricula = request.form.get('matricula')
        especializacao = request.form.get('especializacao')
        formacao = request.form.get('formacao')
        telefone = request.form.get('telefone')
        disciplina_id = request.form.get('disciplina_id')

        if not all([username, email, password, password2, matricula, especializacao, formacao]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        if not validate_username(username):
            flash('Nome de usuário inválido. Deve ter entre 3 e 20 caracteres alfanuméricos.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        user_exists_username = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user_exists_username:
            flash('Este nome de usuário já existe.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

        new_user = User(
            matricula=matricula,
            username=username, 
            email=email, 
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        success, message = InstrutorService.save_instrutor(new_user.id, request.form.to_dict())

        if success:
            if disciplina_id and disciplina_id.isdigit():
                DisciplinaService.update_disciplina_instrutor(int(disciplina_id), new_user.id)
            flash('Instrutor cadastrado com sucesso!', 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            db.session.rollback()
            flash(f"Erro ao cadastrar perfil do instrutor: {message}", 'error')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

    return render_template('cadastro_instrutor.html', form_data={}, disciplinas=disciplinas, is_admin_flow=True)

@instrutor_bp.route('/listar')
@login_required
@admin_required
def listar_instrutores():
    instrutores = InstrutorService.get_all_instrutores()
    return render_template('listar_instrutores.html', instrutores=instrutores)

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))
    
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        disciplina_id = request.form.get('disciplina_id')
        
        success, message = InstrutorService.update_instrutor(instrutor_id, form_data)
        if success:
            if disciplina_id and disciplina_id.isdigit():
                DisciplinaService.update_disciplina_instrutor(int(disciplina_id), instrutor.user_id)
            else:
                DisciplinaService.remove_instrutor_from_disciplina(instrutor.user_id)

            flash(message, 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            flash(message, 'error')
            return render_template('editar_instrutor.html', instrutor=instrutor, form_data=request.form, disciplinas=disciplinas)
            
    return render_template('editar_instrutor.html', instrutor=instrutor, form_data={}, disciplinas=disciplinas)

