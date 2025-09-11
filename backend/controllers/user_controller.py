from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.database import db
from ..models.user import User
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__, url_prefix='/usuario')

@user_bp.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        credor = request.form.get('credor') # <-- CAPTURADO
        
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_nova_senha = request.form.get('confirmar_nova_senha')

        # Atualiza informações básicas
        current_user.nome_completo = nome_completo
        current_user.email = email

        if current_user.role == 'aluno' and current_user.aluno_profile:
            current_user.aluno_profile.telefone = telefone
        elif current_user.role == 'instrutor' and current_user.instrutor_profile:
            current_user.instrutor_profile.telefone = telefone
            current_user.instrutor_profile.credor = credor # <-- SALVO

        # Lógica para alteração de senha
        if senha_atual and nova_senha and confirmar_nova_senha:
            if not current_user.check_password(senha_atual):
                flash('A senha atual está incorreta.', 'danger')
            elif nova_senha != confirmar_nova_senha:
                flash('A nova senha e a confirmação não coincidem.', 'danger')
            else:
                current_user.set_password(nova_senha)
                flash('Senha alterada com sucesso!', 'success')
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('user.meu_perfil'))

    return render_template('meu_perfil.html')