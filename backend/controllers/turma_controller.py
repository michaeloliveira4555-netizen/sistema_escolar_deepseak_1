from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select, or_

from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from utils.decorators import admin_or_programmer_required

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

@turma_bp.route('/')
@login_required
@admin_or_programmer_required
def listar_turmas():
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas)

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

        # Verifica se já existe uma turma com o mesmo nome
        turma_existente = db.session.execute(
            select(Turma).filter_by(nome=nome_turma)
        ).scalar_one_or_none()

        if turma_existente:
            flash(f'Uma turma com o nome "{nome_turma}" já existe.', 'danger')
            return redirect(url_for('turma.cadastrar_turma'))

        nova_turma = Turma(nome=nome_turma, ano=int(ano))
        db.session.add(nova_turma)
        db.session.commit() # Commit para que a nova_turma.id seja gerada

        # Vincula os alunos selecionados à nova turma
        if alunos_ids:
            for aluno_id in alunos_ids:
                aluno = db.session.get(Aluno, int(aluno_id))
                if aluno:
                    aluno.turma_id = nova_turma.id
            db.session.commit()
            
        flash('Turma cadastrada com sucesso!', 'success')
        return redirect(url_for('turma.listar_turmas'))

    # Para o GET, busca alunos que ainda não pertencem a nenhuma turma
    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0))
    ).all()
    return render_template('cadastrar_turma.html', alunos_sem_turma=alunos_sem_turma)