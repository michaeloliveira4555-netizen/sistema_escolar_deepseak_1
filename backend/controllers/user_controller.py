from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.database import db
from ..models.user import User
from werkzeug.security import check_password_hash
from ..services.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='/usuario')

@user_bp.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        success, message = UserService.update_user_profile(current_user, request.form)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('user.meu_perfil'))

    return render_template('meu_perfil.html')