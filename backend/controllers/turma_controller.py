from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select, or_
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget

from ..models.database import db
from ..models.turma import Turma
from ..models.aluno import Aluno
from ..models.disciplina_turma import DisciplinaTurma
from ..models.instrutor import Instrutor
from ..models.disciplina import Disciplina
from ..models.turma_cargo import TurmaCargo
from utils.decorators import admin_or_programmer_required
from ..services.turma_service import TurmaService

turma_bp = Blueprint('turma', __name__, url_prefix='/turma')

CARGOS_LISTA = [
    "Auxiliar do Pelotão", "Chefe de Turma", "C1", "C2", "C3", "C4", "C5"
]

# Forms
class TurmaForm(FlaskForm):
    nome = StringField('Nome da Turma', validators=[DataRequired(), Length(max=100)])
    ano = IntegerField('Ano da Turma', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    alunos_ids = SelectMultipleField('Alunos da Turma', coerce=int, validators=[Optional()],
                                     option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False))
    submit = SubmitField('Salvar Turma')

class TurmaCargoForm(FlaskForm):
    # Fields will be dynamically added in the view
    submit = SubmitField('Salvar Cargos')

class DeleteForm(FlaskForm):
    pass

@turma_bp.route('/')
@login_required
def listar_turmas():
    delete_form = DeleteForm()
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas, delete_form=delete_form)

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

    form = TurmaCargoForm()
    return render_template(
        'detalhes_turma.html',
        turma=turma,
        cargos_lista=CARGOS_LISTA,
        cargos_atuais=cargos_atuais,
        form=form
    )

@turma_bp.route('/<int:turma_id>/salvar-cargos', methods=['POST'])
@login_required
@admin_or_programmer_required
def salvar_cargos_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    form = TurmaCargoForm()

    if form.validate_on_submit():
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
    else:
        flash('Falha na validação do token CSRF ou dados inválidos.', 'danger')

    return redirect(url_for('turma.detalhes_turma', turma_id=turma_id))

@turma_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastrar_turma():
    form = TurmaForm()
    alunos_sem_turma = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0))
    ).all()
    form.alunos_ids.choices = [(a.id, a.user.nome_completo) for a in alunos_sem_turma]

    if form.validate_on_submit():
        success, message = TurmaService.create_turma(request.form)
        if success:
            flash(message, 'success')
            return redirect(url_for('turma.listar_turmas'))
        else:
            flash(message, 'danger')

    return render_template('cadastrar_turma.html', form=form, alunos_sem_turma=alunos_sem_turma)

@turma_bp.route('/editar/<int:turma_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    form = TurmaForm(obj=turma)
    alunos_disponiveis = db.session.scalars(
        select(Aluno).where(or_(Aluno.turma_id == None, Aluno.turma_id == 0, Aluno.turma_id == turma_id))
    ).all()
    form.alunos_ids.choices = [(a.id, a.user.nome_completo) for a in alunos_disponiveis]

    if form.validate_on_submit():
        # Verifica se o novo nome já existe em outra turma
        turma_existente = db.session.execute(
            select(Turma).where(Turma.nome == form.nome.data, Turma.id != turma_id)
        ).scalar_one_or_none()

        if turma_existente:
            flash(f'Já existe outra turma com o nome "{form.nome.data}".', 'danger')
        else:
            turma.nome = form.nome.data
            turma.ano = form.ano.data
            
            # Desvincula todos os alunos atuais
            for aluno in turma.alunos:
                aluno.turma_id = None
            
            # Vincula os novos alunos selecionados
            for aluno_id in form.alunos_ids.data:
                aluno = db.session.get(Aluno, int(aluno_id))
                if aluno:
                    aluno.turma_id = turma.id

            db.session.commit()
            flash('Turma atualizada com sucesso!', 'success')
            return redirect(url_for('turma.listar_turmas'))

    # Para o GET, preenche os alunos selecionados no formulário
    if request.method == 'GET':
        form.alunos_ids.data = [a.id for a in turma.alunos]

    return render_template('editar_turma.html', form=form, turma=turma, alunos_disponiveis=alunos_disponiveis)

@turma_bp.route('/excluir/<int:turma_id>', methods=['POST'])
@login_required
@admin_or_programmer_required
def excluir_turma(turma_id):
    form = DeleteForm()
    if form.validate_on_submit():
        success, message = TurmaService.delete_turma(turma_id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Falha na validação do token CSRF.', 'danger')
    return redirect(url_for('turma.listar_turmas'))