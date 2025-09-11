from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select

from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.horario import Horario
from ..models.historico_disciplina import HistoricoDisciplina
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required

disciplina_bp = Blueprint('disciplina', __name__, url_prefix='/disciplina')

@disciplina_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def adicionar_disciplina():
    if request.method == 'POST':
        success, message = DisciplinaService.save_disciplina(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'danger')
            return render_template('adicionar_disciplina.html', form_data=request.form)
    
    return render_template('adicionar_disciplina.html')

@disciplina_bp.route('/listar')
@login_required
def listar_disciplinas():
    pelotao_filtrado = request.args.get('pelotao')
    disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()
    disciplinas_com_instrutores = []
    if pelotao_filtrado:
        for disciplina in disciplinas:
            associacao = db.session.execute(
                select(DisciplinaTurma).where(
                    DisciplinaTurma.disciplina_id == disciplina.id,
                    DisciplinaTurma.pelotao == pelotao_filtrado
                )
            ).scalar_one_or_none()
            disciplinas_com_instrutores.append((disciplina, associacao))
    else:
        for disciplina in disciplinas:
            disciplinas_com_instrutores.append((disciplina, None))
    return render_template(
        'listar_disciplinas.html', 
        disciplinas_com_instrutores=disciplinas_com_instrutores, 
        pelotao_filtrado=pelotao_filtrado
    )

@disciplina_bp.route('/editar/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_disciplina(disciplina_id):
    disciplina = db.session.get(Disciplina, disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    if request.method == 'POST':
        carga_horaria_str = request.form.get('carga_horaria')
        if carga_horaria_str and carga_horaria_str.isdigit():
            disciplina.carga_horaria_prevista = int(carga_horaria_str)
            db.session.commit()
            flash(f'Carga horária da disciplina "{disciplina.materia}" atualizada com sucesso!', 'success')
        else:
            flash('Valor inválido para carga horária.', 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))

    return render_template('editar_disciplina.html', disciplina=disciplina)

@disciplina_bp.route('/editar-nome/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_nome_disciplina(disciplina_id):
    """Rota para editar apenas o nome e carga horária da disciplina"""
    disciplina = db.session.get(Disciplina, disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    if request.method == 'POST':
        success, message = DisciplinaService.update_disciplina(disciplina_id, request.form.to_dict())
        if success:
            flash(message, 'success')
            return redirect(url_for('disciplina.listar_disciplinas'))
        else:
            flash(message, 'danger')
            return render_template('editar_nome_disciplina.html', disciplina=disciplina, form_data=request.form)
    
    return render_template('editar_nome_disciplina.html', disciplina=disciplina)

@disciplina_bp.route('/excluir/<int:disciplina_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_disciplina(disciplina_id):
    """Excluir disciplina e todos os dados relacionados"""
    disciplina = db.session.get(Disciplina, disciplina_id)
    if not disciplina:
        flash("Disciplina não encontrada.", 'danger')
        return redirect(url_for('disciplina.listar_disciplinas'))
    
    try:
        disciplina_nome = disciplina.materia
        
        # 1. Remover associações disciplina-turma
        associacoes = db.session.scalars(
            select(DisciplinaTurma).where(DisciplinaTurma.disciplina_id == disciplina_id)
        ).all()
        for associacao in associacoes:
            db.session.delete(associacao)
        
        # 2. Remover aulas agendadas
        aulas = db.session.scalars(
            select(Horario).where(Horario.disciplina_id == disciplina_id)
        ).all()
        for aula in aulas:
            db.session.delete(aula)
        
        # 3. Remover histórico de disciplinas dos alunos
        historicos = db.session.scalars(
            select(HistoricoDisciplina).where(HistoricoDisciplina.disciplina_id == disciplina_id)
        ).all()
        for historico in historicos:
            db.session.delete(historico)
        
        # 4. Finalmente, remover a disciplina
        db.session.delete(disciplina)
        
        db.session.commit()
        
        flash(f'Disciplina "{disciplina_nome}" e todos os dados relacionados foram excluídos com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir disciplina: {str(e)}', 'danger')
    
    return redirect(url_for('disciplina.listar_disciplinas'))