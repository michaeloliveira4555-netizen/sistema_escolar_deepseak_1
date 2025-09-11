from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select
from datetime import datetime, timedelta
import re

from ..models.database import db
from ..models.semana import Semana
from utils.decorators import admin_or_programmer_required
from ..services.semana_service import SemanaService

semana_bp = Blueprint('semana', __name__, url_prefix='/semana')

@semana_bp.route('/gerenciar')
@login_required
@admin_or_programmer_required
def gerenciar_semanas():
    semanas = SemanaService.get_all_semanas()
    return render_template('gerenciar_semanas.html', semanas=semanas)

@semana_bp.route('/adicionar', methods=['POST'])
@login_required
@admin_or_programmer_required
def adicionar_semana():
    nome = request.form.get('nome')
    data_inicio_str = request.form.get('data_inicio')
    data_fim_str = request.form.get('data_fim')

    success, message = SemanaService.add_semana(nome, data_inicio_str, data_fim_str)
    if success:
        db.session.commit()
        flash(message, 'success')
    else:
        db.session.rollback()
        flash(message, 'danger')
    
    return redirect(url_for('semana.gerenciar_semanas'))

@semana_bp.route('/adicionar-proxima', methods=['POST'])
@login_required
@admin_or_programmer_required
def adicionar_proxima_semana():
    success, message = SemanaService.add_proxima_semana()

    if success:
        db.session.commit()
        flash(message, 'success')
    else:
        db.session.rollback()
        flash(message, 'danger')

    return redirect(url_for('semana.gerenciar_semanas'))

@semana_bp.route('/editar/<int:semana_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_semana(semana_id):
    semana = SemanaService.get_semana_by_id(semana_id)
    if not semana:
        flash('Semana não encontrada.', 'danger')
        return redirect(url_for('semana.gerenciar_semanas'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')

        success, message = SemanaService.update_semana(semana_id, nome, data_inicio_str, data_fim_str)
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            db.session.rollback()
            flash(message, 'danger')
        return redirect(url_for('semana.gerenciar_semanas'))
    
    return render_template('editar_semana.html', semana=semana)


@semana_bp.route('/deletar/<int:semana_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def deletar_semana(semana_id):
    success, message = SemanaService.delete_semana(semana_id)
    if success:
        db.session.commit()
        flash(message, 'success')
    else:
        db.session.rollback()
        flash(message, 'danger')
    return redirect(url_for('semana.gerenciar_semanas'))