from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..models.database import db
from ..models.instrutor import Instrutor
from ..models.turma import Turma
from ..models.disciplina import Disciplina
from ..models.disciplina_turma import DisciplinaTurma
from utils.decorators import admin_or_programmer_required

vinculo_bp = Blueprint('vinculo', __name__, url_prefix='/vinculos')

@vinculo_bp.route('/')
@login_required
@admin_or_programmer_required
def gerenciar_vinculos():
    turma_filtrada = request.args.get('turma', '')
    disciplina_filtrada_id = request.args.get('disciplina_id', '')

    query = db.select(DisciplinaTurma).options(
        joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
        joinedload(DisciplinaTurma.disciplina)
    ).filter(DisciplinaTurma.instrutor_id_1.isnot(None))

    if turma_filtrada:
        query = query.filter(DisciplinaTurma.pelotao == turma_filtrada)

    if disciplina_filtrada_id:
        query = query.filter(DisciplinaTurma.disciplina_id == int(disciplina_filtrada_id))

    query = query.order_by(DisciplinaTurma.pelotao, DisciplinaTurma.disciplina_id)

    vinculos = db.session.scalars(query).all()

    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()

    return render_template(
        'gerenciar_vinculos.html',
        vinculos=vinculos,
        turmas=turmas,
        disciplinas=disciplinas,
        turma_filtrada=turma_filtrada,
        disciplina_filtrada_id=int(disciplina_filtrada_id) if disciplina_filtrada_id else None
    )

@vinculo_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def adicionar_vinculo():
    if request.method == 'POST':
        instrutor_id = request.form.get('instrutor_id')
        turma_id = request.form.get('turma_id')
        disciplina_id = request.form.get('disciplina_id')

        if not all([instrutor_id, turma_id, disciplina_id]):
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('vinculo.adicionar_vinculo'))

        turma = db.session.get(Turma, int(turma_id))
        if not turma:
            flash('Turma não encontrada.', 'danger')
            return redirect(url_for('vinculo.adicionar_vinculo'))

        vinculo_existente = DisciplinaTurma.query.filter_by(
            disciplina_id=int(disciplina_id),
            pelotao=turma.nome
        ).first()

        if vinculo_existente:
            vinculo_existente.instrutor_id_1 = int(instrutor_id)
            flash('Vínculo atualizado com sucesso!', 'info')
        else:
            novo_vinculo = DisciplinaTurma(
                instrutor_id_1=int(instrutor_id),
                pelotao=turma.nome,
                disciplina_id=int(disciplina_id)
            )
            db.session.add(novo_vinculo)
            flash('Vínculo criado com sucesso!', 'success')

        db.session.commit()
        return redirect(url_for('vinculo.gerenciar_vinculos'))

    instrutores = db.session.scalars(select(Instrutor).order_by(Instrutor.id)).all()
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('adicionar_vinculo.html', instrutores=instrutores, turmas=turmas, ciclos=[1, 2, 3])

@vinculo_bp.route('/editar/<int:vinculo_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_vinculo(vinculo_id):
    vinculo = db.session.get(DisciplinaTurma, vinculo_id)
    if not vinculo:
        flash('Vínculo não encontrado.', 'danger')
        return redirect(url_for('vinculo.gerenciar_vinculos'))

    if request.method == 'POST':
        instrutor_id = request.form.get('instrutor_id')
        turma_id = request.form.get('turma_id')
        disciplina_id = request.form.get('disciplina_id')

        if not all([instrutor_id, turma_id, disciplina_id]):
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('vinculo.editar_vinculo', vinculo_id=vinculo_id))

        turma = db.session.get(Turma, int(turma_id))
        if not turma:
            flash('Turma não encontrada.', 'danger')
            return redirect(url_for('vinculo.editar_vinculo', vinculo_id=vinculo_id))

        vinculo.instrutor_id_1 = int(instrutor_id)
        vinculo.pelotao = turma.nome
        vinculo.disciplina_id = int(disciplina_id)
        db.session.commit()

        flash('Vínculo atualizado com sucesso!', 'success')
        return redirect(url_for('vinculo.gerenciar_vinculos'))

    instrutores = db.session.scalars(select(Instrutor)).all()
    turmas = db.session.scalars(select(Turma)).all()
    disciplina_atual = db.session.get(Disciplina, vinculo.disciplina_id)
    return render_template('editar_vinculo.html', vinculo=vinculo, instrutores=instrutores, turmas=turmas, ciclos=[1, 2, 3], ciclo_atual=disciplina_atual.ciclo)

@vinculo_bp.route('/excluir/<int:vinculo_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_vinculo(vinculo_id):
    vinculo = db.session.get(DisciplinaTurma, vinculo_id)
    if vinculo:
        # Em vez de deletar, apenas remove o instrutor para manter a associação
        vinculo.instrutor_id_1 = None
        vinculo.instrutor_id_2 = None
        db.session.commit()
        flash('Vínculo de instrutor removido com sucesso!', 'success')
    else:
        flash('Vínculo não encontrado.', 'danger')
    return redirect(url_for('vinculo.gerenciar_vinculos'))