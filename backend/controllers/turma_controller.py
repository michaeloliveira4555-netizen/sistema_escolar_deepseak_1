from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_

from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from utils.decorators import admin_or_programmer_required

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

@turma_bp.route('/')
@login_required
def listar_turmas():
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas)

# CORREÇÃO: Decorator de admin removido para permitir a visualização por alunos
@turma_bp.route('/<int:turma_id>')
@login_required
def detalhes_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
        
    instrutores = db.session.scalars(select(Instrutor).order_by(Instrutor.id)).all()
    
    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(Aluno.turma_id == None)
    ).all()
    
    todas_as_disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()
    
    associacoes_existentes = db.session.scalars(
        select(DisciplinaTurma).where(DisciplinaTurma.pelotao == turma.nome)
    ).all()
    
    associacoes_dict = {assoc.disciplina_id: assoc for assoc in associacoes_existentes}
    
    disciplinas_para_template = []
    
    for disciplina in todas_as_disciplinas:
        if disciplina.id not in associacoes_dict:
            nova_associacao = DisciplinaTurma(
                pelotao=turma.nome,
                disciplina_id=disciplina.id
            )
            db.session.add(nova_associacao)
            disciplinas_para_template.append(nova_associacao)
        else:
            disciplinas_para_template.append(associacoes_dict[disciplina.id])
            
    db.session.commit()
    disciplinas_para_template.sort(key=lambda dt: dt.disciplina.materia)

    disciplinas_com_dois_instrutores = ["AMT I", "AMT II", "Atendimento Pré-Hospitalar Tático"]

    return render_template(
        'detalhes_turma.html', 
        turma=turma,
        instrutores=instrutores,
        disciplinas_turma=disciplinas_para_template,
        disciplinas_com_dois_instrutores=disciplinas_com_dois_instrutores,
        alunos_sem_turma=alunos_sem_turma
    )

# As rotas abaixo permanecem restritas a administradores
@turma_bp.route('/<int:turma_id>/adicionar-alunos-pagina')
@login_required
@admin_or_programmer_required
def adicionar_alunos_turma_pagina(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
    
    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(Aluno.turma_id == None).order_by(Aluno.id)
    ).all()

    return render_template('adicionar_aluno_turma.html', turma=turma, alunos_sem_turma=alunos_sem_turma)

@turma_bp.route('/<int:turma_id>/adicionar-alunos', methods=['POST'])
@login_required
@admin_or_programmer_required
def adicionar_alunos_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
    
    alunos_ids_para_adicionar = request.form.getlist('aluno_ids')
    if not alunos_ids_para_adicionar:
        flash('Nenhum aluno selecionado para adicionar.', 'warning')
        return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

    try:
        for aluno_id in alunos_ids_para_adicionar:
            aluno = db.session.get(Aluno, int(aluno_id))
            if aluno:
                aluno.turma_id = turma_id
        
        db.session.commit()
        flash(f'{len(alunos_ids_para_adicionar)} aluno(s) adicionado(s) à turma com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar alunos: {e}', 'danger')

    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/<int:turma_id>/remover-alunos', methods=['POST'])
@login_required
@admin_or_programmer_required
def remover_alunos_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    alunos_ids_para_remover = request.form.getlist('aluno_ids')
    if not alunos_ids_para_remover:
        flash('Nenhum aluno selecionado para remover.', 'warning')
        return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

    try:
        for aluno_id in alunos_ids_para_remover:
            aluno = db.session.get(Aluno, int(aluno_id))
            if aluno and aluno.turma_id == turma_id:
                aluno.turma_id = None
                
        db.session.commit()
        flash(f'{len(alunos_ids_para_remover)} aluno(s) removido(s) da turma com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover alunos: {e}', 'danger')

    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/<int:turma_id>/editar-disciplinas', methods=['POST'])
@login_required
@admin_or_programmer_required
def editar_disciplinas_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    todas_as_disciplinas = db.session.scalars(select(Disciplina)).all()

    for disciplina in todas_as_disciplinas:
        instrutor_id_1_str = request.form.get(f'instrutor1_{disciplina.id}')
        instrutor_id_2_str = request.form.get(f'instrutor2_{disciplina.id}')

        instrutor_id_1 = int(instrutor_id_1_str) if instrutor_id_1_str else None
        instrutor_id_2 = int(instrutor_id_2_str) if instrutor_id_2_str else None

        disciplina_turma = db.session.scalars(
            select(DisciplinaTurma).where(
                DisciplinaTurma.pelotao == turma.nome,
                DisciplinaTurma.disciplina_id == disciplina.id
            )
        ).first()

        if not instrutor_id_1:
            if disciplina_turma:
                db.session.delete(disciplina_turma)
        else:
            if disciplina_turma:
                disciplina_turma.instrutor_id_1 = instrutor_id_1
                disciplina_turma.instrutor_id_2 = instrutor_id_2
            else:
                nova_associacao = DisciplinaTurma(
                    pelotao=turma.nome,
                    disciplina_id=disciplina.id,
                    instrutor_id_1=instrutor_id_1,
                    instrutor_id_2=instrutor_id_2
                )
                db.session.add(nova_associacao)

    try:
        db.session.commit()
        flash('Instrutores da turma atualizados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar as alterações: {e}', 'danger')

    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastrar_turma():
    if request.method == 'POST':
        nome_turma = request.form.get('nome')
        ano = request.form.get('ano')
        alunos_ids = request.form.getlist('alunos_ids')

        if not nome_turma or not ano:
            flash('Nome da turma e ano são obrigatórios.', 'danger')
            return redirect(url_for('turma.cadastrar_turma'))

        turma_existente = db.session.execute(
            select(Turma).filter_by(nome=nome_turma)
        ).scalar_one_or_none()

        if turma_existente:
            flash(f'Uma turma com o nome "{nome_turma}" já existe.', 'danger')
            return redirect(url_for('turma.cadastrar_turma'))

        nova_turma = Turma(nome=nome_turma, ano=int(ano))
        db.session.add(nova_turma)
        db.session.commit() 

        if alunos_ids:
            for aluno_id in alunos_ids:
                aluno = db.session.get(Aluno, int(aluno_id))
                if aluno:
                    aluno.turma_id = nova_turma.id
            db.session.commit()
            
        flash('Turma cadastrada com sucesso!', 'success')
        return redirect(url_for('turma.listar_turmas'))

    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0))
    ).all()
    return render_template('cadastrar_turma.html', alunos_sem_turma=alunos_sem_turma)