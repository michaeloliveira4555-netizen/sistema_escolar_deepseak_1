from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo

from ..models.database import db
from ..models.user import User
from werkzeug.security import check_password_hash
from ..services.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='/usuario')

# Forms
class UserProfileForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Senha Atual', validators=[Optional()])
    new_password = PasswordField('Nova Senha', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nova Senha', validators=[EqualTo('new_password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Atualizar Perfil')

@user_bp.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    form = UserProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Update basic profile info
        current_user.nome_completo = form.nome_completo.data
        current_user.email = form.email.data

        # Handle password change
        if form.current_password.data or form.new_password.data or form.confirm_new_password.data:
            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('user.meu_perfil'))
            
            if form.new_password.data != form.confirm_new_password.data:
                flash('As novas senhas não coincidem.', 'danger')
                return redirect(url_for('user.meu_perfil'))

            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('user.meu_perfil'))

    return render_template('meu_perfil.html', form=form)