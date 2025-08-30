from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from ..app import db
from ..models.user import User
from utils.validators import validate_username, validate_email, validate_password_strength

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        # Pega o papel do formulário, mas garante que não seja 'admin' se for enviado
        requested_role = request.form.get('role', 'aluno')
        role = requested_role if requested_role in ['aluno', 'instrutor'] else 'aluno'

        if not all([username, email, password, password2]):
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('auth.register'))

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('auth.register'))
        
        if not validate_username(username):
            flash('Nome de usuário inválido. Deve ter entre 3 e 20 caracteres alfanuméricos.', 'danger')
            return redirect(url_for('auth.register'))
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return redirect(url_for('auth.register'))
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return redirect(url_for('auth.register'))

        user_exists_username = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user_exists_username:
            flash('Este nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.register'))
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('login.html')

        user = db.session.execute(db.select(User).filter_by(username=username)).scalar()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login'))