from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select
from datetime import datetime

from ..models.database import db
from ..models.semana import Semana
from utils.decorators import admin_or_programmer_required

semana_bp = Blueprint('semana', __name__, url_prefix='/semana')

@semana_bp.route('/gerenciar')
@login_required
@admin_or_programmer_required
def gerenciar_semanas():
    semanas = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()
    return render_template('gerenciar_semanas.html', semanas=semanas)

@semana_bp.route('/adicionar', methods=['POST'])
@login_required
@admin_or_programmer_required
def adicionar_semana():
    nome = request.form.get('nome')
    data_inicio_str = request.form.get('data_inicio')
    data_fim_str = request.form.get('data_fim')

    if not all([nome, data_inicio_str, data_fim_str]):
        flash('Todos os campos são obrigatórios.', 'danger')
        return redirect(url_for('semana.gerenciar_semanas'))

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
        return redirect(url_for('semana.gerenciar_semanas'))

    nova_semana = Semana(nome=nome, data_inicio=data_inicio, data_fim=data_fim)
    db.session.add(nova_semana)
    db.session.commit()
    
    flash('Nova semana cadastrada com sucesso!', 'success')
    return redirect(url_for('semana.gerenciar_semanas'))

@semana_bp.route('/deletar/<int:semana_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def deletar_semana(semana_id):
    semana = db.session.get(Semana, semana_id)
    if semana:
        # Adicionar verificação se a semana está em uso antes de deletar
        db.session.delete(semana)
        db.session.commit()
        flash('Semana deletada com sucesso.', 'success')
    else:
        flash('Semana não encontrada.', 'danger')
    return redirect(url_for('semana.gerenciar_semanas'))