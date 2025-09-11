from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from ..services.user_service import UserService
from ..forms import PreRegistrationForm
from utils.decorators import admin_or_programmer_required

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
    form = PreRegistrationForm()
    if form.validate_on_submit():
        success, message = UserService.pre_register_user(form)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('main.pre_cadastro'))

    return render_template('pre_cadastro.html', form=form)