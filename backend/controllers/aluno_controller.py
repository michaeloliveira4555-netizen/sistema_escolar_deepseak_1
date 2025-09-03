from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

# Mantemos as importações necessárias
from ..extensions import db
from ..services.aluno_service import AlunoService
from ..models.user import User
from utils.decorators import admin_required
from utils.validators import validate_email, validate_password_strength

aluno_bp = Blueprint('aluno', __name__, url_prefix='/aluno')

# Decorator atualizado para aceitar programador
def admin_or_programmer_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        user_role = getattr(current_user, 'role', None)
        if user_role not in ['admin', 'programador']:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@aluno_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = AlunoService.save_aluno(current_user.id, form_data)

        if success:
            flash(message, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'error')
            return render_template('cadastro_aluno.html', form_data=form_data)

    return render_template('cadastro_aluno.html', form_data={})

@aluno_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_aluno_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = 'aluno' 
        
        matricula = request.form.get('matricula')
        opm = request.form.get('opm')
        pelotao = request.form.get('pelotao')
        funcao_atual = request.form.get('funcao_atual')
        form_data = request.form.to_dict()
        foto = request.files.get('foto_perfil')

        if not all([email, password, password2, matricula, opm, pelotao]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        user_exists_matricula = db.session.execute(db.select(User).filter_by(matricula=matricula)).scalar_one_or_none()
        if user_exists_matricula:
            flash('Esta matrícula já está em uso.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        new_user = User(
            matricula=matricula,
            username=matricula, 
            email=email, 
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        success, message = AlunoService.save_aluno(new_user.id, form_data, foto)

        if success:
            flash('Aluno cadastrado com sucesso!', 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            db.session.rollback()
            flash(f"Erro ao cadastrar perfil do aluno: {message}", 'error')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

    return render_template('cadastro_aluno_admin.html', form_data={})

@aluno_bp.route('/listar')
@login_required
@admin_or_programmer_required
def listar_alunos():
    pelotao_filtrado = request.args.get('pelotao', None)
    alunos = AlunoService.get_all_alunos(pelotao_filtrado)
    return render_template('listar_alunos.html', alunos=alunos, pelotao_filtrado=pelotao_filtrado)

@aluno_bp.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_aluno(aluno_id):
    aluno = AlunoService.get_aluno_by_id(aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('aluno.listar_alunos'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        foto = request.files.get('foto_perfil')
        success, message = AlunoService.update_aluno(aluno_id, form_data, foto)
        if success:
            flash(message, 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            flash(message, 'error')
            return render_template('editar_aluno.html', aluno=aluno, form_data=request.form)
            
    return render_template('editar_aluno.html', aluno=aluno, form_data={})