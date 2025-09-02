from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..app import db
from ..models.user import User
from ..models.instrutor import Instrutor

instrutor_bp = Blueprint('instrutor', __name__, url_prefix='/instrutor')

@instrutor_bp.route('/listar')
@login_required
def listar_instrutores():
    instrutores = db.session.execute(db.select(Instrutor).order_by(Instrutor.nome_completo)).scalars().all()
    return render_template('listar_instrutores.html', instrutores=instrutores)

@instrutor_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_instrutor():
    if request.method == 'POST':
        # Dados para a tabela User
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        # Dados para a tabela Instrutor
        nome_completo = request.form.get('nome_completo')
        matricula_instrutor = request.form.get('matricula_instrutor')
        especializacao = request.form.get('especializacao')

        # Validações
        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastrar_instrutor.html', form_data=request.form)

        user_exists = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_exists:
            flash('Este e-mail já está em uso.', 'danger')
            return render_template('cadastrar_instrutor.html', form_data=request.form)

        # Cria o User
        new_user = User(
            matricula=matricula_instrutor, # Usamos a matrícula do instrutor como identificador principal
            email=email,
            username=email, # Podemos usar o email como username inicial
            role='instrutor',
            is_active=True
        )
        new_user.set_password(password)
        
        # Cria o Instrutor e associa ao User
        novo_instrutor = Instrutor(
            user=new_user,
            nome_completo=nome_completo,
            matricula_instrutor=matricula_instrutor,
            especializacao=especializacao
        )
        
        db.session.add(novo_instrutor) # Adicionando o instrutor, o user virá junto pela relação
        db.session.commit()
        
        flash('Instrutor cadastrado com sucesso!', 'success')
        return redirect(url_for('instrutor.listar_instrutores'))

    return render_template('cadastrar_instrutor.html')

@instrutor_bp.route('/editar/<int:instrutor_id>', methods=['GET', 'POST'])
@login_required
def editar_instrutor(instrutor_id):
    instrutor = db.session.get(Instrutor, instrutor_id)
    if not instrutor:
        flash('Instrutor não encontrado.', 'danger')
        return redirect(url_for('instrutor.listar_instrutores'))

    if request.method == 'POST':
        instrutor.nome_completo = request.form.get('nome_completo')
        instrutor.matricula_instrutor = request.form.get('matricula_instrutor')
        instrutor.especializacao = request.form.get('especializacao')
        instrutor.user.email = request.form.get('email')
        
        db.session.commit()
        flash('Dados do instrutor atualizados com sucesso!', 'success')
        return redirect(url_for('instrutor.listar_instrutores'))

    return render_template('editar_instrutor.html', instrutor=instrutor)

@instrutor_bp.route('/deletar/<int:instrutor_id>', methods=['POST'])
@login_required
def deletar_instrutor(instrutor_id):
    instrutor = db.session.get(Instrutor, instrutor_id)
    if instrutor:
        # A relação cascade no modelo User deve apagar o instrutor junto.
        db.session.delete(instrutor.user)
        db.session.commit()
        flash('Instrutor removido com sucesso.', 'success')
    else:
        flash('Instrutor não encontrado.', 'danger')
    return redirect(url_for('instrutor.listar_instrutores'))