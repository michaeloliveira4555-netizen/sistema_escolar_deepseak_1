from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..models.database import db
from ..models.user import User
from ..services.instrutor_service import InstrutorService
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required
from utils.validators import validate_email, validate_password_strength

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

@instrutor_bp.route('/listar')
@login_required
def listar_instrutores():
    instrutores = InstrutorService.get_all_instrutores()
    return render_template('listar_instrutores.html', instrutores=instrutores)

# NOVA ROTA ADICIONADA
@instrutor_bp.route('/completar-cadastro', methods=['GET', 'POST'])
@login_required
def completar_cadastro():
    # Se o perfil já existe, não deixa o usuário acessar esta página
    if current_user.instrutor_profile:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = InstrutorService.save_instrutor(current_user.id, form_data)

        if success:
            flash("Perfil de instrutor completado com sucesso!", 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'danger')
            return render_template('completar_cadastro_instrutor.html')

    return render_template('completar_cadastro_instrutor.html')


@instrutor_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_instrutor_admin():
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo')
        matricula = request.form.get('matricula')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = 'instrutor'

        especializacao = request.form.get('especializacao')
        formacao = request.form.get('formacao')

        if not all([nome_completo, matricula, email, password, password2]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, is_admin_flow=True)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, is_admin_flow=True)

        new_user = User(
            id_func=matricula,
            username=matricula,
            nome_completo=nome_completo,
            email=email,
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        success, message = InstrutorService.save_instrutor(new_user.id, request.form.to_dict())

        if success:
            flash('Instrutor cadastrado com sucesso!', 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            db.session.delete(new_user)
            db.session.commit()
            flash(f"Erro ao cadastrar perfil do instrutor: {message}", 'error')
            return render_template('cadastro_instrutor.html', form_data=request.form, is_admin_flow=True)

    return render_template('cadastro_instrutor.html', form_data={}, is_admin_flow=True)

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))

    if request.method == 'POST':
        success, message = InstrutorService.update_instrutor(instrutor_id, request.form.to_dict())

        if success:
            flash(message, 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            flash(message, 'error')
            return render_template('editar_instrutor.html', instrutor=instrutor, form_data=request.form)

    return render_template('editar_instrutor.html', instrutor=instrutor)

@instrutor_bp.route('/excluir/<int:instrutor_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))

    try:
        user_a_deletar = instrutor.user
        db.session.delete(user_a_deletar)
        db.session.commit()
        flash('Instrutor excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir instrutor: {e}', 'danger')

    return redirect(url_for('instrutor.listar_instrutores'))