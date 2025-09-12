from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..app import db
# IMPORTAÇÃO DO NOVO DECORADOR
from utils.decorators import aluno_profile_required, admin_or_programmer_required
from ..services.user_service import UserService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    dashboard_data = {}
    return render_template('dashboard.html', dashboard_data=dashboard_data)

@main_bp.route('/pre-cadastro', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def pre_cadastro():
    if request.method == 'POST':
        success, message = UserService.pre_register_user(request.form)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('main.pre_cadastro'))

    return render_template('pre_cadastro.html')