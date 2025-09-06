from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import select

# Mantemos as importações necessárias
from ..models.database import db
from ..services.aluno_service import AlunoService
from ..models.user import User
from ..models.turma import Turma # Adicionado para buscar as turmas
from utils.decorators import admin_or_programmer_required
from utils.validators import validate_email, validate_password_strength

aluno_bp = Blueprint('aluno', __name__, url_prefix='/aluno')

@aluno_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    # Esta rota é para o próprio aluno completar o perfil após o registro
    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = AlunoService.save_aluno(current_user.id, form_data)

        if success:
            flash(message, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'error')
    
    # Busca turmas para o aluno selecionar
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('cadastro_aluno.html', form_data={}, turmas=turmas)

@aluno_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_aluno_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = 'aluno' 
        
        matricula = request.form.get('matricula')
        opm = request.form.get('opm')
        turma_id = request.form.get('turma_id')
        funcao_atual = request.form.get('funcao_atual')

        if not all([email, password, password2, matricula, opm]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
            return render_template('cadastro_aluno_admin.html', form_data=request.form, turmas=turmas)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
            return render_template('cadastro_aluno_admin.html', form_data=request.form, turmas=turmas)
        
        # Outras validações...
        user_exists_matricula = db.session.execute(db.select(User).filter_by(matricula=matricula)).scalar_one_or_none()
        if user_exists_matricula:
            flash('Esta matrícula já está em uso.', 'danger')
            turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
            return render_template('cadastro_aluno_admin.html', form_data=request.form, turmas=turmas)

        new_user = User(
            matricula=matricula,
            username=matricula, 
            email=email, 
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Passa os dados do formulário, incluindo o turma_id
        success, message = AlunoService.save_aluno(new_user.id, request.form.to_dict())

        if success:
            flash('Aluno cadastrado com sucesso!', 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            # Se a criação do perfil do aluno falhar, remove o usuário criado
            db.session.delete(new_user)
            db.session.commit()
            flash(f"Erro ao cadastrar perfil do aluno: {message}", 'error')
            turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
            return render_template('cadastro_aluno_admin.html', form_data=request.form, turmas=turmas)

    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('cadastro_aluno_admin.html', form_data={}, turmas=turmas)

@aluno_bp.route('/listar')
@login_required
@admin_or_programmer_required
def listar_alunos():
    turma_filtrada = request.args.get('turma', None)
    alunos = AlunoService.get_all_alunos(turma_filtrada)
    
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    
    return render_template('listar_alunos.html', alunos=alunos, turmas=turmas, turma_filtrada=turma_filtrada)

@aluno_bp.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_aluno(aluno_id):
    aluno = AlunoService.get_aluno_by_id(aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('aluno.listar_alunos'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = AlunoService.update_aluno(aluno_id, form_data)
        if success:
            flash(message, 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            flash(message, 'error')
            # Retorna os dados do formulário para que o usuário não precise preencher tudo de novo
            turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
            return render_template('editar_aluno.html', aluno=aluno, turmas=turmas, form_data=request.form)
            
    # Na requisição GET, passa o objeto aluno para o formulário
    turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    return render_template('editar_aluno.html', aluno=aluno, turmas=turmas, form_data=aluno)