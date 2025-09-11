from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_

from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from ..models.turma_cargo import TurmaCargo
from utils.decorators import admin_or_programmer_required

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

CARGOS_LISTA = [
    "Auxiliar do Pelotão", "Chefe de Turma", "C1", "C2", "C3", "C4", "C5"
]

@turma_bp.route('/')
@login_required
def listar_turmas():
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas)

@turma_bp.route('/<int:turma_id>')
@login_required
def detalhes_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    cargos_db = db.session.scalars(
        select(TurmaCargo).where(TurmaCargo.turma_id == turma_id)
    ).all()
    cargos_atuais = {cargo.cargo_nome: cargo.aluno_id for cargo in cargos_db}

    for cargo in CARGOS_LISTA:
        if cargo not in cargos_atuais:
            cargos_atuais[cargo] = None

    return render_template(
        'detalhes_turma.html',
        turma=turma,
        cargos_lista=CARGOS_LISTA,
        cargos_atuais=cargos_atuais
    )

@turma_bp.route('/<int:turma_id>/salvar-cargos', methods=['POST'])
@login_required
@admin_or_programmer_required
def salvar_cargos_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    try:
        for cargo_nome in CARGOS_LISTA:
            aluno_id_str = request.form.get(f'cargo_{cargo_nome}')
            aluno_id = int(aluno_id_str) if aluno_id_str else None

            cargo_existente = db.session.scalars(
                select(TurmaCargo).where(
                    TurmaCargo.turma_id == turma_id,
                    TurmaCargo.cargo_nome == cargo_nome
                )
            ).first()

            if cargo_existente:
                cargo_existente.aluno_id = aluno_id
            else:
                novo_cargo = TurmaCargo(
                    turma_id=turma_id,
                    cargo_nome=cargo_nome,
                    aluno_id=aluno_id
                )
                db.session.add(novo_cargo)

        db.session.commit()
        flash('Cargos da turma atualizados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar os cargos: {e}', 'danger')

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

@turma_bp.route('/editar/<int:turma_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        novo_ano = request.form.get('ano')
        novos_alunos_ids = set(request.form.getlist('alunos_ids'))

        # Verifica se o novo nome já existe em outra turma
        turma_existente = db.session.execute(
            select(Turma).where(Turma.nome == novo_nome, Turma.id != turma_id)
        ).scalar_one_or_none()

        if turma_existente:
            flash(f'Já existe outra turma com o nome "{novo_nome}".', 'danger')
            return redirect(url_for('turma.editar_turma', turma_id=turma_id))
        
        turma.nome = novo_nome
        turma.ano = int(novo_ano)
        
        # Desvincula todos os alunos atuais
        for aluno in turma.alunos:
            aluno.turma_id = None
        
        # Vincula os novos alunos selecionados
        for aluno_id in novos_alunos_ids:
            aluno = db.session.get(Aluno, int(aluno_id))
            if aluno:
                aluno.turma_id = turma.id

        db.session.commit()
        flash('Turma atualizada com sucesso!', 'success')
        return redirect(url_for('turma.listar_turmas'))

    # Para o GET, lista os alunos desta turma e os alunos sem turma
    alunos_disponiveis = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0, Aluno.turma_id == turma_id))
    ).all()

    return render_template('editar_turma.html', turma=turma, alunos_disponiveis=alunos_disponiveis)


@turma_bp.route('/excluir/<int:turma_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    try:
        nome_turma_excluida = turma.nome
        for aluno in turma.alunos:
            aluno.turma_id = None
        db.session.query(TurmaCargo).filter_by(turma_id=turma_id).delete()
        db.session.query(DisciplinaTurma).filter_by(pelotao=turma.nome).delete()
        db.session.delete(turma)
        db.session.commit()
        flash(f'Turma "{nome_turma_excluida}" e todos os seus vínculos foram excluídos com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir a turma: {str(e)}', 'danger')

    return redirect(url_for('turma.listar_turmas'))