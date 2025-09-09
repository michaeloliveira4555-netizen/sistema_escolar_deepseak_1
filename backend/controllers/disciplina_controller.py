from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select

from ..models.database import db
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
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
@login_required # Permite que todos os logados acessem
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
    
    disciplinas_com_dois_instrutores = ["AMT I", "AMT II", "Atendimento Pré-Hospitalar Tático"]
    
    if request.method == 'POST':
        carga_horaria_str = request.form.get('carga_horaria')
        if carga_horaria_str and carga_horaria_str.isdigit():
            disciplina.carga_horaria_prevista = int(carga_horaria_str)
        
        db.session.query(DisciplinaTurma).filter_by(disciplina_id=disciplina.id).delete()
        for i in range(1, 11):
            pelotao_nome = f'{i}° Pelotão'
            instrutor_id_1_str = request.form.get(f'pelotao_{i}_instrutor_1')
            instrutor_id_2_str = request.form.get(f'pelotao_{i}_instrutor_2')
            
            if instrutor_id_1_str and instrutor_id_1_str.isdigit():
                nova_atribuicao = DisciplinaTurma(
                    pelotao=pelotao_nome,
                    disciplina_id=disciplina.id,
                    instrutor_id_1=int(instrutor_id_1_str),
                    instrutor_id_2=int(instrutor_id_2_str) if instrutor_id_2_str and instrutor_id_2_str.isdigit() else None
                )
                db.session.add(nova_atribuicao)
        
        db.session.commit()
        flash(f'Atribuições da disciplina "{disciplina.materia}" atualizadas com sucesso!', 'success')
        return redirect(url_for('disciplina.listar_disciplinas'))

    instrutores = db.session.scalars(select(Instrutor).order_by(Instrutor.id)).all()
    atribuicoes_existentes = db.session.scalars(
        select(DisciplinaTurma).where(DisciplinaTurma.disciplina_id == disciplina.id)
    ).all()
    
    atribuicoes = {atr.pelotao: atr for atr in atribuicoes_existentes}
    
    return render_template(
        'editar_disciplina.html', 
        disciplina=disciplina, 
        instrutores=instrutores,
        atribuicoes=atribuicoes,
        disciplinas_com_dois_instrutores=disciplinas_com_dois_instrutores
    )