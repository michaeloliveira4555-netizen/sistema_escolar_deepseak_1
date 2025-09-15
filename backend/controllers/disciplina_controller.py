from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
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
            # Redireciona para o ciclo da disciplina recém-criada
            ciclo = request.form.get('ciclo', 1)
            return redirect(url_for('disciplina.listar_disciplinas', ciclo=ciclo))
        else:
            flash(message, 'danger')
            return render_template('adicionar_disciplina.html', form_data=request.form)
    
    return render_template('adicionar_disciplina.html')

@disciplina_bp.route('/listar')
@login_required
def listar_disciplinas():
    # Obtém o ciclo da URL ou da sessão do usuário, com padrão 1
    ciclo_selecionado = request.args.get('ciclo', session.get('ultimo_ciclo_visualizado', 1), type=int)
    session['ultimo_ciclo_visualizado'] = ciclo_selecionado # Salva a escolha do usuário

    pelotao_filtrado = request.args.get('pelotao')
    
    # Filtra as disciplinas pelo ciclo selecionado
    disciplinas = db.session.scalars(
        select(Disciplina).where(Disciplina.ciclo == ciclo_selecionado).order_by(Disciplina.materia)
    ).all()
    
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
        pelotao_filtrado=pelotao_filtrado,
        ciclos=[1, 2, 3],
        ciclo_selecionado=ciclo_selecionado
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
        return redirect(url_for('disciplina.listar_disciplinas', ciclo=disciplina.ciclo))

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
            return redirect(url_for('disciplina.listar_disciplinas', ciclo=disciplina.ciclo))
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
        ciclo_redirect = disciplina.ciclo
        disciplina_nome = disciplina.materia
        
        # Remover associações, aulas e históricos
        db.session.query(DisciplinaTurma).filter_by(disciplina_id=disciplina_id).delete()
        db.session.query(Horario).filter_by(disciplina_id=disciplina_id).delete()
        db.session.query(HistoricoDisciplina).filter_by(disciplina_id=disciplina_id).delete()
        
        db.session.delete(disciplina)
        
        db.session.commit()
        
        flash(f'Disciplina "{disciplina_nome}" e todos os dados relacionados foram excluídos com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir disciplina: {str(e)}', 'danger')
    
    return redirect(url_for('disciplina.listar_disciplinas', ciclo=ciclo_redirect))