# backend/controllers/historico_controller.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models.database import db
from ..models.historico_disciplina import HistoricoDisciplina
from ..services.historico_service import HistoricoService
from ..services.aluno_service import AlunoService
from utils.decorators import admin_or_programmer_required

historico_bp = Blueprint('historico', __name__, url_prefix='/historico')

@historico_bp.route('/aluno/<int:aluno_id>')
@login_required
def historico_aluno(aluno_id):
    # Lógica para verificar se o usuário pode ver o histórico
    user_role = getattr(current_user, 'role', None)
    is_admin = user_role in ['super_admin', 'programador', 'admin_escola']
    is_own_profile = hasattr(current_user, 'aluno_profile') and current_user.aluno_profile and current_user.aluno_profile.id == aluno_id

    if not (is_admin or is_own_profile):
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
    # A lógica de verificação de permissão deve estar DENTRO da rota
    registro = db.session.get(HistoricoDisciplina, historico_id)
    if not registro:
        flash("Registro de avaliação não encontrado.", 'danger')
        return redirect(url_for('main.dashboard'))

    # Apenas o próprio aluno pode salvar suas notas (ou um admin no futuro)
    is_own_profile = hasattr(current_user, 'aluno_profile') and current_user.aluno_profile.id == registro.aluno_id
    is_admin = getattr(current_user, 'role', None) in ['super_admin', 'programador', 'admin_escola']

    if not (is_own_profile or is_admin):
        flash("Você não tem permissão para realizar esta ação.", 'danger')
        return redirect(url_for('main.dashboard'))

    # Delega a lógica de salvamento para o serviço
    form_data = request.form.to_dict()
    success, message, aluno_id = HistoricoService.avaliar_aluno(historico_id, form_data)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    if aluno_id:
        return redirect(url_for('historico.historico_aluno', aluno_id=aluno_id))
    else:
        # Fallback para o dashboard se o aluno_id não for encontrado
        return redirect(url_for('main.dashboard'))