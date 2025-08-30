from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from ..services.dashboard_service import DashboardService

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    role = getattr(current_user, 'role', None)
    dashboard_data = None
    if role == 'admin':
        dashboard_data = DashboardService.get_dashboard_data()

    if role == 'aluno' and not (hasattr(current_user, 'aluno_profile') and current_user.aluno_profile):
        flash('Bem-vindo! Por favor, complete seu perfil de aluno para continuar.', 'info')
        return redirect(url_for('aluno.cadastro_aluno'))
    
    if role == 'instrutor' and not (hasattr(current_user, 'instrutor_profile') and current_user.instrutor_profile):
        flash('Bem-vindo! Por favor, complete seu perfil de instrutor para continuar.', 'info')
        return redirect(url_for('instrutor.cadastro_instrutor'))

    return render_template('dashboard.html', user=current_user, dashboard_data=dashboard_data)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))