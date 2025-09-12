from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional

from ..models.database import db
from ..models.user import User
from ..services.instrutor_service import InstrutorService
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required
from utils.validators import validate_email, validate_password_strength

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

# Forms
class InstrutorProfileForm(FlaskForm):
    especializacao = StringField('Especialização', validators=[DataRequired(), Length(max=100)])
    formacao = StringField('Formação', validators=[DataRequired(), Length(max=100)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(max=20)])
    credor = TextAreaField('Credor (Informações de Pagamento)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Salvar Perfil')

class InstrutorAdminForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    matricula = StringField('Matrícula (Id Funcional)', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repita a Senha', validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    especializacao = StringField('Especialização', validators=[DataRequired(), Length(max=100)])
    formacao = StringField('Formação', validators=[DataRequired(), Length(max=100)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(max=20)])
    credor = TextAreaField('Credor (Informações de Pagamento)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Cadastrar Instrutor')

class DeleteForm(FlaskForm):
    submit = SubmitField('Excluir')

@instrutor_bp.route('/listar')
@login_required
def listar_instrutores():
    delete_form = DeleteForm()
    instrutores = InstrutorService.get_all_instrutores()
    return render_template('listar_instrutores.html', instrutores=instrutores, delete_form=delete_form)

@instrutor_bp.route('/completar-cadastro', methods=['GET', 'POST'])
@login_required
def completar_cadastro():
    if current_user.instrutor_profile:
        return redirect(url_for('main.dashboard'))

    form = InstrutorProfileForm()
    if form.validate_on_submit():
        success, message = InstrutorService.save_instrutor(current_user.id, form.data)
        if success:
            flash("Perfil de instrutor completado com sucesso!", 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'danger')
    return render_template('completar_cadastro_instrutor.html', form=form)

@instrutor_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_instrutor_admin():
    form = InstrutorAdminForm()
    if form.validate_on_submit():
        is_strong, message = validate_password_strength(form.password.data)
        if not is_strong:
            flash(message, 'danger')
            return render_template('cadastro_instrutor.html', form=form, is_admin_flow=True)

        if User.query.filter_by(id_func=form.matricula.data).first():
            flash('Esta matrícula (Id Funcional) já está em uso.', 'danger')
            return render_template('cadastro_instrutor.html', form=form, is_admin_flow=True)

        try:
            new_user = User(
                id_func=form.matricula.data,
                username=form.matricula.data,
                nome_completo=form.nome_completo.data,
                email=form.email.data,
                role='instrutor',
                is_active=True
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.flush()

            success, message = InstrutorService.save_instrutor(new_user.id, form.data)

            if success:
                db.session.commit()
                flash('Instrutor cadastrado com sucesso!', 'success')
                return redirect(url_for('instrutor.listar_instrutores'))
            else:
                db.session.rollback()
                flash(f"Erro ao cadastrar perfil do instrutor: {message}", 'error')
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro inesperado: {e}", 'danger')

    return render_template('cadastro_instrutor.html', form=form, is_admin_flow=True)

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))

    form = InstrutorProfileForm(obj=instrutor)
    if form.validate_on_submit():
        success, message = InstrutorService.update_instrutor(instrutor_id, form.data)
        if success:
            flash(message, 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            flash(message, 'error')

    return render_template('editar_instrutor.html', form=form, instrutor=instrutor)

@instrutor_bp.route('/excluir/<int:instrutor_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_instrutor(instrutor_id):
    form = DeleteForm()
    if form.validate_on_submit():
        success, message = InstrutorService.delete_instrutor(instrutor_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Falha na validação do token CSRF.', 'danger')
    return redirect(url_for('instrutor.listar_instrutores'))