from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..models.database import db
from ..models.user import User
from ..services.instrutor_service import InstrutorService
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required
from utils.validators import validate_email, validate_password_strength

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

# ... (o resto do controller que não foi alterado) ...

@instrutor_bp.route('/cadastro_admin', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def cadastro_instrutor_admin():
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        # ### LÓGICA ATUALIZADA ###
        nome_completo = request.form.get('nome_completo')
        matricula = request.form.get('matricula')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = 'instrutor'

        especializacao = request.form.get('especializacao')
        formacao = request.form.get('formacao')
        telefone = request.form.get('telefone')
        disciplina_id = request.form.get('disciplina_id')

        # Agora validamos o nome completo também
        if not all([nome_completo, matricula, email, password, password2, especializacao, formacao]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        if not validate_email(email):
            flash('Formato de e-mail inválido.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        is_valid_password, password_message = validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        user_exists_matricula = db.session.execute(db.select(User).filter_by(matricula=matricula)).scalar_one_or_none()
        if user_exists_matricula:
            flash('Esta matrícula já está em uso.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)
        
        user_exists_email = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists_email:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

        new_user = User(
            matricula=matricula,
            username=matricula,  # Matrícula também é o nome de usuário
            nome_completo=nome_completo, # Novo campo
            email=email, 
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        # Commit aqui para garantir que o user.id seja gerado antes de salvar o instrutor
        db.session.commit()

        # Passamos os dados do formulário para o serviço criar o perfil do instrutor
        success, message = InstrutorService.save_instrutor(new_user.id, request.form.to_dict())

        if success:
            if disciplina_id and disciplina_id.isdigit():
                # Precisamos buscar o instrutor recém-criado para associar a disciplina
                instrutor_profile = new_user.instrutor_profile
                if instrutor_profile:
                    DisciplinaService.update_disciplina_instrutor(int(disciplina_id), instrutor_profile.id)
            flash('Instrutor cadastrado com sucesso!', 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            # Se a criação do perfil do instrutor falhar, removemos o usuário criado
            db.session.delete(new_user)
            db.session.commit()
            flash(f"Erro ao cadastrar perfil do instrutor: {message}", 'error')
            return render_template('cadastro_instrutor.html', form_data=request.form, disciplinas=disciplinas, is_admin_flow=True)

    return render_template('cadastro_instrutor.html', form_data={}, disciplinas=disciplinas, is_admin_flow=True)

# ... (o resto do controller que não foi alterado) ...

@instrutor_bp.route('/listar')
@login_required
@admin_or_programmer_required
def listar_instrutores():
    instrutores = InstrutorService.get_all_instrutores()
    return render_template('listar_instrutores.html', instrutores=instrutores)

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_instrutor(instrutor_id):
    instrutor = InstrutorService.get_instrutor_by_id(instrutor_id)
    if not instrutor:
        flash("Instrutor não encontrado.", 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))
    
    disciplinas = DisciplinaService.get_all_disciplinas()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        disciplina_id = request.form.get('disciplina_id')
        
        success, message = InstrutorService.update_instrutor(instrutor_id, form_data)
        if success:
            if disciplina_id and disciplina_id.isdigit():
                DisciplinaService.update_disciplina_instrutor(int(disciplina_id), instrutor.user_id)
            else:
                DisciplinaService.remove_instrutor_from_disciplina(instrutor.user_id)

            flash(message, 'success')
            return redirect(url_for('instrutor.listar_instrutores'))
        else:
            flash(message, 'error')
            return render_template('editar_instrutor.html', instrutor=instrutor, form_data=request.form, disciplinas=disciplinas)
            
    return render_template('editar_instrutor.html', instrutor=instrutor, form_data={}, disciplinas=disciplinas)