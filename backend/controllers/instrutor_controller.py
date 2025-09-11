from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from ..models.database import db
from ..services.instrutor_service import InstrutorService
from ..forms import InstrutorForm, EditInstrutorForm
from utils.decorators import admin_or_programmer_required

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

@instrutor_bp.route('/listar')
@login_required
def listar_instrutores():
    instrutores = InstrutorService.get_all_instrutores()
    return render_template('listar_instrutores.html', instrutores=instrutores)

@instrutor_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_instrutor_admin():
    form = InstrutorForm()
    if form.validate_on_submit():
        success, message = InstrutorService.create_instrutor_with_user(form)
        if success:
            flash(message, 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            flash(message, 'error')

    return render_template('cadastro_instrutor.html', form=form)

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))
    
    form = EditInstrutorForm(obj=instrutor)
    if form.validate_on_submit():
        success, message = InstrutorService.update_instrutor(instrutor_id, form)
        
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