from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
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
@admin_or_programmer_required
def listar_turmas():
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('listar_turmas.html', turmas=turmas)

@turma_bp.route('/<int:turma_id>')
@login_required
@admin_or_programmer_required
def detalhes_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))
        
    instrutores = db.session.scalars(select(Instrutor).order_by(Instrutor.id)).all()
    
    # 1. Pega todas as disciplinas que existem no sistema
    todas_as_disciplinas = db.session.scalars(select(Disciplina).order_by(Disciplina.materia)).all()
    
    # 2. Pega as associações que JÁ existem para esta turma
    associacoes_existentes = db.session.scalars(
        select(DisciplinaTurma).where(DisciplinaTurma.pelotao == turma.nome)
    ).all()
    
    associacoes_dict = {assoc.disciplina_id: assoc for assoc in associacoes_existentes}
    
    disciplinas_para_template = []
    
    # 3. Garante que TODAS as disciplinas tenham uma associação com a turma
    for disciplina in todas_as_disciplinas:
        if disciplina.id not in associacoes_dict:
            # Se a associação não existe, cria na hora
            nova_associacao = DisciplinaTurma(
                pelotao=turma.nome,
                disciplina_id=disciplina.id
            )
            db.session.add(nova_associacao)
            disciplinas_para_template.append(nova_associacao)
        else:
            # Se já existe, apenas adiciona na lista para exibição
            disciplinas_para_template.append(associacoes_dict[disciplina.id])
            
    # Salva no banco de dados qualquer nova associação que tenha sido criada
    db.session.commit()
    
    # Ordena a lista final por nome da matéria para uma exibição consistente
    disciplinas_para_template.sort(key=lambda dt: dt.disciplina.materia)

    disciplinas_com_dois_instrutores = ["AMT I", "AMT II", "Atendimento Pré-Hospitalar Tático"]

    return render_template(
        'detalhes_turma.html', 
        turma=turma,
        instrutores=instrutores,
        disciplinas_turma=disciplinas_para_template,
        disciplinas_com_dois_instrutores=disciplinas_com_dois_instrutores
    )

@turma_bp.route('/<int:turma_id>/editar-disciplinas', methods=['POST'])
@login_required
@admin_or_programmer_required
def editar_disciplinas_turma(turma_id):
    turma = db.session.get(Turma, turma_id)
    if not turma:
        flash('Turma não encontrada.', 'danger')
        return redirect(url_for('turma.listar_turmas'))

    for key, value in request.form.items():
        if key.startswith('instrutor1_'):
            disciplina_turma_id = key.split('_')[1]
            instrutor_id_1 = value
            
            disciplina_turma = db.session.get(DisciplinaTurma, disciplina_turma_id)
            if disciplina_turma:
                disciplina_turma.instrutor_id_1 = int(instrutor_id_1) if instrutor_id_1 and instrutor_id_1.isdigit() else None
        
        elif key.startswith('instrutor2_'):
            disciplina_turma_id = key.split('_')[1]
            instrutor_id_2 = value
            
            disciplina_turma = db.session.get(DisciplinaTurma, disciplina_turma_id)
            if disciplina_turma:
                disciplina_turma.instrutor_id_2 = int(instrutor_id_2) if instrutor_id_2 and instrutor_id_2.isdigit() else None

    db.session.commit()
    flash('Instrutores da turma atualizados com sucesso!', 'success')
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