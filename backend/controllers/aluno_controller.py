from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash # Importado para criar senhas de novos usuários

from ..app import db # CORREÇÃO: Adicionada a importação do objeto db
from ..services.aluno_service import AlunoService
from ..models.user import User # Importado para criar novos usuários
from utils.decorators import admin_required
from utils.validators import validate_username, validate_email, validate_password_strength # Importado para validação

aluno_bp = Blueprint('aluno', __name__, url_prefix='/aluno')

@aluno_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    # Esta rota é para o próprio aluno completar seu perfil após o registro inicial.
    # A lógica de redirecionamento para completar perfil já está no main.dashboard.
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
@admin_required
def cadastro_aluno_admin():
    if request.method == 'POST':
        # Dados do Usuário
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role', 'aluno')

        # Dados do Aluno
        matricula = request.form.get('matricula')
        opm = request.form.get('opm')
        pelotao = request.form.get('pelotao')
        funcao_atual = request.form.get('funcao_atual')

        # --- Validações ---
        if not all([username, email, password, password2, matricula, opm, pelotao]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        if not validate_username(username):
            flash('Nome de usuário inválido. Deve ter entre 3 e 20 caracteres alfanuméricos.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        user_exists_username = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user_exists_username:
            flash('Este nome de usuário já existe.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        success, message = AlunoService.save_aluno(new_user.id, request.form.to_dict())

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
@admin_required
def listar_alunos():
    pelotao_filtrado = request.args.get('pelotao', None)
    alunos = AlunoService.get_all_alunos(pelotao_filtrado)
    return render_template('listar_alunos.html', alunos=alunos, pelotao_filtrado=pelotao_filtrado)

@aluno_bp.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_aluno(aluno_id):
    aluno = AlunoService.get_aluno_by_id(aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('aluno.listar_alunos'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = AlunoService.update_aluno(aluno_id, form_data)
        if success:
            flash(message, 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            flash(message, 'error')
            return render_template('editar_aluno.html', aluno=aluno, form_data=request.form)
            
    return render_template('editar_aluno.html', aluno=aluno, form_data={})
