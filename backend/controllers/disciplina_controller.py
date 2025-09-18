from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from ..models.database import db
from ..models.disciplina import Disciplina
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

# Forms
class DisciplinaForm(FlaskForm):
    materia = StringField('Matéria', validators=[DataRequired(), Length(min=3, max=100)])
    carga_horaria_prevista = IntegerField('Carga Horária Prevista', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Salvar')

class DeleteForm(FlaskForm):
    pass

@disciplina_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def adicionar_disciplina():
    form = DisciplinaForm()
    if form.validate_on_submit():
        success, message = DisciplinaService.save_disciplina(form.data)
        if success:
            flash(message, 'success')
            # Redireciona para o ciclo da disciplina recém-criada
            ciclo = request.form.get('ciclo', 1)
            return redirect(url_for('disciplina.listar_disciplinas', ciclo=ciclo))
        else:
            flash(message, 'danger')
    return render_template('adicionar_disciplina.html', form=form)

@disciplina_bp.route('/listar')
@login_required
def listar_disciplinas():

    delete_form = DeleteForm()
    pelotao_filtrado = request.args.get('pelotao')
    disciplinas = DisciplinaService.get_all_disciplinas_com_associacoes(pelotao_filtrado)
    disciplinas_com_instrutores = []
    if pelotao_filtrado:
        for disciplina in disciplinas:
            associacao = next((a for a in disciplina.associacoes_turmas if a.pelotao == pelotao_filtrado), None)
            disciplinas_com_instrutores.append((disciplina, associacao))
    else:
        for disciplina in disciplinas:
            disciplinas_com_instrutores.append((disciplina, None))
            
    return render_template(
        'listar_disciplinas.html', 
        disciplinas_com_instrutores=disciplinas_com_instrutores, 
        pelotao_filtrado=pelotao_filtrado,
        delete_form=delete_form
    )

# Rota de API para buscar disciplinas por ciclo (usado na tela de vínculos)
@disciplina_bp.route('/api/por-ciclo/<int:ciclo_id>')
@login_required
@admin_or_programmer_required
def api_disciplinas_por_ciclo(ciclo_id):
    disciplinas = db.session.scalars(
        select(Disciplina).where(Disciplina.ciclo == ciclo_id).order_by(Disciplina.materia)
    ).all()
    return jsonify([{'id': d.id, 'materia': d.materia} for d in disciplinas])


@disciplina_bp.route('/editar/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_disciplina(disciplina_id):

    disciplina = DisciplinaService.get_disciplina_by_id(disciplina_id)

    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    form = DisciplinaForm(obj=disciplina)
    if form.validate_on_submit():
        success, message = DisciplinaService.update_disciplina(disciplina_id, form.data)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas', ciclo=disciplina.ciclo))
        else:
            flash(message, 'danger')

    return render_template('editar_disciplina.html', form=form, disciplina=disciplina)

@disciplina_bp.route('/excluir/<int:disciplina_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_disciplina(disciplina_id):

    form = DeleteForm()
    if form.validate_on_submit():
        success, message = DisciplinaService.delete_disciplina(disciplina_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Falha na validação do token CSRF.', 'danger')
    return redirect(url_for('disciplina.listar_disciplinas'))

