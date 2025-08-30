from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

# Mantemos as importações necessárias
from ..app import db
from ..services.aluno_service import AlunoService
from ..models.user import User
from utils.decorators import admin_required
from utils.validators import validate_email, validate_password_strength

aluno_bp = Blueprint('aluno', __name__, url_prefix='/aluno')

# --- NENHUMA ALTERAÇÃO NECESSÁRIA NESTA ROTA ---
# Esta rota é para o aluno completar o próprio perfil.
@aluno_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = AlunoService.save_aluno(current_user.id, form_data)

        if success:
            flash(message, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'error')
            return render_template('cadastro_aluno.html', form_data=form_data)

    return render_template('cadastro_aluno.html', form_data={})

# --- ESTA ROTA FOI COMPLETAMENTE ATUALIZADA ---
# Rota para o admin cadastrar um novo aluno.
@aluno_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_required
def cadastro_aluno_admin():
    if request.method == 'POST':
        # --- Coleta de Dados do Formulário ---
        # REMOVIDO: Não pegamos mais o 'username' do formulário.
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        # ALTERADO: O 'role' agora é fixo como 'aluno' para esta rota.
        role = 'aluno' 
        
        # O campo 'matricula' agora é a chave principal para o login.
        matricula = request.form.get('matricula')
        opm = request.form.get('opm')
        pelotao = request.form.get('pelotao')
        funcao_atual = request.form.get('funcao_atual')

        # --- Validações ---
        if not all([email, password, password2, matricula, opm, pelotao]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        # NOVA VALIDAÇÃO: Verificar se a matrícula já existe no sistema.
        user_exists_matricula = db.session.execute(db.select(User).filter_by(matricula=matricula)).scalar_one_or_none()
        if user_exists_matricula:
            flash('Esta matrícula já está em uso.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

        # --- Criação do Usuário ---
        # ALTERADO: Usamos a matrícula como username.
        new_user = User(
            username=matricula, 
            email=email, 
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        # Commit inicial para gerar o ID do new_user
        db.session.commit()

        # Salva as informações específicas do aluno
        success, message = AlunoService.save_aluno(new_user.id, request.form.to_dict())

        if success:
            flash('Aluno cadastrado com sucesso!', 'success')
            return redirect(url_for('aluno.listar_alunos'))
        else:
            # Se o save_aluno falhar, desfazemos a criação do usuário
            db.session.rollback()
            flash(f"Erro ao cadastrar perfil do aluno: {message}", 'error')
            return render_template('cadastro_aluno_admin.html', form_data=request.form)

    return render_template('cadastro_aluno_admin.html', form_data={})


# --- NENHUMA ALTERAÇÃO NECESSÁRIA NESTA ROTA ---
@aluno_bp.route('/listar')
@login_required
@admin_required
def listar_alunos():
    pelotao_filtrado = request.args.get('pelotao', None)
    alunos = AlunoService.get_all_alunos(pelotao_filtrado)
    return render_template('listar_alunos.html', alunos=alunos, pelotao_filtrado=pelotao_filtrado)


# --- NENHUMA ALTERAÇÃO NECESSÁRIA NESTA ROTA ---
@aluno_bp.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
@admin_required
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
            return render_template('editar_aluno.html', aluno=aluno, form_data=request.form)
            
    return render_template('editar_aluno.html', aluno=aluno, form_data={})