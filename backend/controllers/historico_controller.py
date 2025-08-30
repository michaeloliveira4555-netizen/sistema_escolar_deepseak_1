from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..app import db # CORREÇÃO: Adicionada a importação do objeto db
from ..services.historico_service import HistoricoService
from ..services.aluno_service import AlunoService
from ..models.historico_disciplina import HistoricoDisciplina
from utils.decorators import admin_required

historico_bp = Blueprint('historico', __name__, url_prefix='/historico')

@historico_bp.route('/aluno/<int:aluno_id>')
@login_required
def historico_aluno(aluno_id):
    is_admin = getattr(current_user, 'role', None) == 'admin'
    if not (is_admin or (hasattr(current_user, 'aluno_profile') and current_user.aluno_profile and current_user.aluno_profile.id == aluno_id)):
        flash("Você não tem permissão para visualizar este histórico.", 'danger')
        return redirect(url_for('main.dashboard'))

    historico_disciplinas = HistoricoService.get_historico_disciplinas_for_aluno(aluno_id)
    historico_atividades = HistoricoService.get_historico_atividades_for_aluno(aluno_id)
    disciplinas_nao_cursadas = HistoricoService.get_disciplinas_nao_cursadas(aluno_id)
    aluno = AlunoService.get_aluno_by_id(aluno_id)

    if not aluno:
        flash("Aluno não encontrado.", 'danger')
        return redirect(url_for('main.dashboard'))

    return render_template('historico_aluno.html', 
                           aluno=aluno, 
                           historico_disciplinas=historico_disciplinas,
                           historico_atividades=historico_atividades,
                           disciplinas_nao_cursadas=disciplinas_nao_cursadas)

@historico_bp.route('/matricular/<int:aluno_id>', methods=['POST'])
@login_required
@admin_required
def matricular_aluno_em_disciplina(aluno_id):
    disciplina_id_str = request.form.get('disciplina_id')
    success, message = HistoricoService.matricular_aluno(aluno_id, disciplina_id_str)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('historico.historico_aluno', aluno_id=aluno_id))

@historico_bp.route('/avaliar/<int:historico_id>', methods=['POST'])
@login_required
def avaliar_aluno_disciplina(historico_id):
    is_admin = getattr(current_user, 'role', None) == 'admin'
    is_instrutor = getattr(current_user, 'role', None) == 'instrutor'
    
    if not (is_admin or is_instrutor):
        flash("Você não tem permissão para realizar esta ação.", 'danger')
        return redirect(url_for('main.dashboard'))

    form_data = request.form.to_dict()
    success, message, aluno_id = HistoricoService.avaliar_aluno(historico_id, form_data)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('historico.historico_aluno', aluno_id=aluno_id))
