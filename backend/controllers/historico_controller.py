from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models.database import db
from ..services.historico_service import HistoricoService
from ..services.aluno_service import AlunoService

from utils.decorators import admin_or_programmer_required

historico_bp = Blueprint('historico', __name__, url_prefix='/historico')

@historico_bp.route('/aluno/<int:aluno_id>')
@login_required
def historico_aluno(aluno_id):
    user_role = getattr(current_user, 'role', None)

    is_authorized = user_role in ['super_admin', 'programador']
    
    # Verifica se o usuário logado é o próprio aluno

    is_own_profile = hasattr(current_user, 'aluno_profile') and current_user.aluno_profile and current_user.aluno_profile.id == aluno_id

    if not (is_authorized or is_own_profile):
        flash("Você não tem permissão para visualizar este histórico.", 'danger')
        return redirect(url_for('main.dashboard'))

    aluno = AlunoService.get_aluno_by_id(aluno_id)
    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('main.dashboard'))

    historico_disciplinas = HistoricoService.get_historico_disciplinas_for_aluno(aluno_id)
    
    notas_finais = [h.nota for h in historico_disciplinas if h.nota is not None]
    media_final_curso = sum(notas_finais) / len(notas_finais) if notas_finais else 0.0

    return render_template('historico_aluno.html',
                           aluno=aluno,
                           historico_disciplinas=historico_disciplinas,
                           media_final_curso=media_final_curso)


@historico_bp.route('/avaliar/<int:historico_id>', methods=['POST'])
@login_required
def avaliar_aluno_disciplina(historico_id):

    # Verificação de permissão atualizada para incluir 'programador'
    user_role = getattr(current_user, 'role', None)
    is_authorized = user_role in ['super_admin', 'programador', 'instrutor']

    
    # VERIFICAÇÃO DE SEGURANÇA: Garante que apenas o aluno dono do histórico pode salvar
    is_own_profile = current_user.is_authenticated and hasattr(current_user, 'aluno_profile') and current_user.aluno_profile.id == registro.aluno_id

    if not is_own_profile:
        flash("Você não tem permissão para realizar esta ação.", 'danger')
        # Redireciona para o dashboard se não for o dono, ou para o próprio histórico se for outro aluno
        return redirect(url_for('main.dashboard'))

    form_data = request.form.to_dict()
    success, message, aluno_id = HistoricoService.avaliar_aluno(historico_id, form_data)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    if aluno_id:
        return redirect(url_for('historico.historico_aluno', aluno_id=aluno_id))
    else:
        return redirect(url_for('main.dashboard'))