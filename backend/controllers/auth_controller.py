from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required
from sqlalchemy import or_

from ..app import db
from ..models.user import User
from ..forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email_exists = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if email_exists:
            flash('Este e-mail já está em uso por outra conta.', 'danger')
            return render_template('register.html', form=form)

        username_exists = db.session.execute(db.select(User).filter_by(username=form.username.data)).scalar_one_or_none()
        if username_exists:
            flash('Este nome de usuário já está em uso por outra conta.', 'danger')
            return render_template('register.html', form=form)

        user = db.session.execute(
            db.select(User).filter_by(id_func=form.id_func.data, role=form.role.data)
        ).scalar_one_or_none()

        if not user:
            flash('Identidade Funcional não encontrada para a função selecionada. Contate a administração.', 'danger')
            return render_template('register.html', form=form)
        
        if user.is_active:
            flash('Esta conta já foi ativada. Tente fazer o login.', 'info')
            return redirect(url_for('auth.login'))

        user.email = form.email.data
        user.username = form.username.data
        user.set_password(form.password.data)
        user.is_active = True
        
        db.session.commit()

        flash('Sua conta foi ativada com sucesso! Agora você pode fazer o login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter(
            or_(User.id_func == form.login_identifier.data, User.username == form.login_identifier.data)
        )).scalar_one_or_none()

        if user and user.is_active and user.check_password(form.password.data):
            login_user(user)
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