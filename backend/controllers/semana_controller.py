from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select
from datetime import datetime, timedelta
import re

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

@semana_bp.route('/adicionar-proxima', methods=['POST'])
@login_required
@admin_or_programmer_required
def adicionar_proxima_semana():
    ultima_semana = db.session.scalars(select(Semana).order_by(Semana.data_fim.desc())).first()

    if not ultima_semana:
        flash('Para adicionar a "próxima semana", você precisa cadastrar a primeira semana manualmente.', 'warning')
        return redirect(url_for('semana.gerenciar_semanas'))

    # Lógica para o nome da próxima semana
    numeros = re.findall(r'\d+', ultima_semana.nome)
    proximo_numero = int(numeros[-1]) + 1 if numeros else 1
    novo_nome = f"Semana {proximo_numero}"

    # Lógica para a data da próxima semana
    dias_para_proxima_segunda = (7 - ultima_semana.data_fim.weekday()) % 7
    nova_data_inicio = ultima_semana.data_fim + timedelta(days=dias_para_proxima_segunda)
    nova_data_fim = nova_data_inicio + timedelta(days=4) # De segunda a sexta

    nova_semana = Semana(nome=novo_nome, data_inicio=nova_data_inicio, data_fim=nova_data_fim)
    db.session.add(nova_semana)
    db.session.commit()

    flash(f'"{novo_nome}" adicionada com sucesso!', 'success')
    return redirect(url_for('semana.gerenciar_semanas'))

@semana_bp.route('/editar/<int:semana_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_semana(semana_id):
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash('Semana não encontrada.', 'danger')
        return redirect(url_for('semana.gerenciar_semanas'))

    if request.method == 'POST':
        semana.nome = request.form.get('nome')
        semana.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
        semana.data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date()
        db.session.commit()
        flash('Semana atualizada com sucesso!', 'success')
        return redirect(url_for('semana.gerenciar_semanas'))
    
    return render_template('editar_semana.html', semana=semana)


@semana_bp.route('/deletar/<int:semana_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def deletar_semana(semana_id):
    semana = db.session.get(Semana, semana_id)
    if semana:
        db.session.delete(semana)
        db.session.commit()
        flash('Semana deletada com sucesso.', 'success')
    else:
        flash('Semana não encontrada.', 'danger')
    return redirect(url_for('semana.gerenciar_semanas'))