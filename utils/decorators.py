from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def programmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        if not getattr(current_user, 'role', None) == 'programador':
            flash('Acesso restrito para programadores.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_programmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        user_role = getattr(current_user, 'role', None)
        if user_role not in ['super_admin', 'programador']:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# NOVO DECORADOR ADICIONADO
def admin_escola_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        user_role = getattr(current_user, 'role', None)
        if user_role != 'admin_escola':
            flash('Acesso restrito para administradores de escola.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# NOVO DECORADOR ADICIONADO
def aluno_profile_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
            
        if current_user.role == 'aluno':
            if hasattr(current_user, 'aluno_profile') and current_user.aluno_profile:
                return f(*args, **kwargs)
            else:
                flash('Para continuar, por favor, complete seu perfil de aluno.', 'info')
                return redirect(url_for('aluno.cadastro_aluno'))
        else:
            flash('Acesso restrito para alunos.', 'danger')
            return redirect(url_for('main.dashboard'))
    return decorated_function