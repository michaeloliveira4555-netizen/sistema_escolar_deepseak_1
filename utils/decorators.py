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
        if user_role not in ['admin', 'programador']:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# NOVO DECORADOR ADICIONADO
def aluno_profile_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se o usuário não for um aluno, permite o acesso
        if current_user.role != 'aluno':
            return f(*args, **kwargs)
        # Se for um aluno, verifica se o perfil detalhado (aluno_profile) existe
        if hasattr(current_user, 'aluno_profile') and current_user.aluno_profile:
            return f(*args, **kwargs)
        # Se não tiver perfil, força o redirecionamento para a página de cadastro
        else:
            flash('Para continuar, por favor, complete seu perfil de aluno.', 'info')
            return redirect(url_for('aluno.cadastro_aluno'))
    return decorated_function