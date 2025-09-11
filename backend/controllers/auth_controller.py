from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required

from ..app import db
from ..models.user import User
from utils.validators import validate_email, validate_password_strength

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_func = request.form.get('id_func')
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if not role:
            flash('Por favor, selecione sua função (Aluno ou Instrutor).', 'danger')
            return render_template('register.html', form_data=request.form)

        user = db.session.execute(
            db.select(User).filter_by(id_func=id_func, role=role)
        ).scalar_one_or_none()

        if not user:
            flash('Identidade Funcional não encontrada para a função selecionada. Contate a administração.', 'danger')
            return render_template('register.html', form_data=request.form)

        if user.is_active:
            flash('Esta conta já foi ativada. Tente fazer o login.', 'info')
            return redirect(url_for('auth.login'))

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('register.html', form_data=request.form)

        email_exists = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if email_exists and email_exists.id != user.id:
            flash('Este e-mail já está em uso por outra conta.', 'danger')
            return render_template('register.html', form_data=request.form)

        # Ativa a conta
        user.nome_completo = nome_completo
        user.email = email
        user.username = id_func
        user.set_password(password)
        user.is_active = True

        db.session.commit()

        flash('Sua conta foi ativada com sucesso! Agora você pode fazer o login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('username')
        password = request.form.get('password')

        user = db.session.execute(db.select(User).filter_by(id_func=login_identifier)).scalar_one_or_none()

        if not user:
            user = db.session.execute(db.select(User).filter_by(username=login_identifier)).scalar_one_or_none()

        if user and user.is_active and user.check_password(password):
            login_user(user)
            # Se for um aluno sem perfil, redireciona para completar
            if user.role == 'aluno' and not user.aluno_profile:
                flash('Por favor, complete seu perfil de aluno para continuar.', 'info')
                return redirect(url_for('aluno.cadastro_aluno'))
            return redirect(url_for('main.dashboard'))
        elif user and not user.is_active:
            flash('Sua conta precisa ser ativada. Use a página de registro para ativá-la.', 'warning')
        else:
            flash('Id Func/Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))