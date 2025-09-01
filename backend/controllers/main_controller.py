from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Futuramente, aqui virá a lógica para buscar dados do banco
    dashboard_data = {
        'total_users': 0,
        'total_alunos': 0,
        'total_instrutores': 0,
        'total_disciplinas': 0
    }
    return render_template('dashboard.html', dashboard_data=dashboard_data)

# --- NOVO CÓDIGO ADICIONADO ABAIXO ---

@main_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
# @admin_required # Descomente quando o decorador de admin estiver pronto
def pre_cadastro():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem realizar o pré-cadastro.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        raw_matriculas = request.form.get('matriculas', '')
        role = request.form.get('role')

        if not raw_matriculas or not role:
            flash('Por favor, preencha todos os campos.', 'warning')
            return render_template('pre_cadastro.html')

        # Processa a lista de matrículas, removendo espaços e linhas vazias
        matriculas_list = [m.strip() for m in raw_matriculas.splitlines() if m.strip()]
        
        novos_cadastros = 0
        ja_existiam = 0

        for matricula in matriculas_list:
            user_exists = db.session.execute(db.select(User).filter_by(matricula=matricula)).scalar_one_or_none()
            if user_exists:
                ja_existiam += 1
            else:
                new_user = User(
                    matricula=matricula,
                    role=role,
                    is_active=False # A conta é criada como inativa
                )
                db.session.add(new_user)
                novos_cadastros += 1
        
        db.session.commit()

        flash(f'{novos_cadastros} usuários pré-cadastrados com sucesso! {ja_existiam} matrículas já existiam no sistema.', 'success')
        return redirect(url_for('main.pre_cadastro'))

    return render_template('pre_cadastro.html')