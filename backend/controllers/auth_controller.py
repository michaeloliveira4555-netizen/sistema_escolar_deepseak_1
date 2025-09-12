from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from ..app import db, limiter
from ..models.user import User
from utils.validators import validate_email, validate_password_strength

auth_bp = Blueprint('auth', __name__)

# Define o formulário de login
class LoginForm(FlaskForm):
    username = StringField('Id Func / Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_func = request.form.get('id_func')
        nome_completo = request.form.get('nome_tempo')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if not role:
            flash('Por favor, selecione sua função (Aluno ou Instrutor).', 'danger')
            return render_template('register.html', form_data=request.form)

        # Validação do e-mail
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('register.html', form_data=request.form)

        # Validação da senha
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(message, 'danger')
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
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_identifier = form.username.data
        password = form.password.data

        user = db.session.execute(db.select(User).filter_by(id_func=login_identifier)).scalar_one_or_none()

        if not user:
            user = db.session.execute(db.select(User).filter_by(username=login_identifier)).scalar_one_or_none()

        if user and user.is_active and user.check_password(password):
            login_user(user)

            # Se for um aluno sem perfil, redireciona para completar
            if user.role == 'aluno' and not user.aluno_profile:
                flash('Por favor, complete seu perfil de aluno para continuar.', 'info')
                return redirect(url_for('aluno.cadastro_aluno'))
            # SE FOR UM INSTRUTOR SEM PERFIL, REDIRECIONA PARA COMPLETAR
            elif user.role == 'instrutor' and not user.instrutor_profile:
                flash('Por favor, complete seu perfil de instrutor para continuar.', 'info')
                return redirect(url_for('instrutor.completar_cadastro'))

            return redirect(url_for('main.dashboard'))
        elif user and not user.is_active:
            flash('Sua conta precisa ser ativada. Use a página de registro para ativá-la.', 'warning')
        else:
            flash('Id Func/Usuário ou senha inválidos.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))