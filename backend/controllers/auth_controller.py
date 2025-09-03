from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required

from ..app import db
from ..models.user import User
from ..services.aluno_service import AlunoService # IMPORTANTE: Adicionado
from utils.validators import validate_email, validate_password_strength

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        email_local_part = request.form.get('email_local_part', '').strip()
        email = f"{email_local_part}@bm.rs.gov.br"
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if not role:
            flash('Por favor, selecione sua função (Aluno ou Instrutor).', 'danger')
            return render_template('register.html', form_data=request.form)

        user = db.session.execute(
            db.select(User).filter_by(matricula=matricula, role=role)
        ).scalar_one_or_none()

        if not user:
            flash('Identificador não encontrado para a função selecionada. Contate a administração.', 'danger')
            return render_template('register.html', form_data=request.form)
        
        if user.is_active:
            flash('Esta conta já foi ativada. Tente fazer o login.', 'info')
            return redirect(url_for('auth.login'))

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('register.html', form_data=request.form)
        
        email_exists = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if email_exists:
            flash('Este e-mail já está em uso por outra conta.', 'danger')
            return render_template('register.html', form_data=request.form)

        # Ativa a conta User
        user.email = email
        user.username = matricula
        user.set_password(password)
        user.is_active = True
        
        # IMPORTANTE: Salva os dados do perfil do Aluno (pelotão, função, etc.)
        # O AlunoService vai criar um novo perfil de aluno e associá-lo a este usuário
        if role == 'aluno':
            form_data = request.form.to_dict()
            # Precisamos adicionar nome_completo ao form_data, mesmo que vazio, para o service funcionar
            if 'nome_completo' not in form_data:
                form_data['nome_completo'] = "A ser preenchido" # Valor Padrão
            
            success, message = AlunoService.save_aluno(user.id, form_data)
            if not success:
                # Se salvar o perfil do aluno falhar, desfazemos a ativação do usuário
                db.session.rollback() 
                flash(f'Erro ao criar perfil de aluno: {message}', 'danger')
                return render_template('register.html', form_data=request.form)

        db.session.commit()

        flash('Sua conta foi ativada com sucesso! Agora você pode fazer o login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... (código da função login continua o mesmo)
    if request.method == 'POST':
        login_identifier = request.form.get('username')
        password = request.form.get('password')

        user = db.session.execute(db.select(User).filter_by(matricula=login_identifier)).scalar_one_or_none()

        if not user:
            user = db.session.execute(db.select(User).filter_by(username=login_identifier)).scalar_one_or_none()

        if user and user.is_active and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        elif user and not user.is_active:
            flash('Sua conta precisa ser ativada. Use a página de registro para ativá-la.', 'warning')
        else:
            flash('Matrícula/Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))