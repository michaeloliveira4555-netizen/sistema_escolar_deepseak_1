from flask import Blueprint, render_template
from flask_login import login_required
from utils.decorators import admin_or_programmer_required

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

@horario_bp.route('/')
@login_required
@admin_or_programmer_required
def index():
    """Página principal do Quadro Horário."""
    
    # --- LÓGICA ATUALIZADA PARA INCLUIR SÁBADO E DOMINGO ---
    schedule_raw = {
        'segunda': [
            {'materia': 'Gestão e Supervisão pela Qualidade do Serviço', 'instrutor': '1ºSgt PM Fão', 'periodo': 1, 'duracao': 3},
            {'materia': 'Policiamento Ostensivo', 'instrutor': 'Cap PM Silva', 'periodo': 4, 'duracao': 2},
            {'materia': 'Direito Penal Militar', 'instrutor': 'Maj PM Ana', 'periodo': 7, 'duracao': 1},
        ],
        'terca': [
            {'materia': 'Gestão e Supervisão pela Qualidade do Serviço', 'instrutor': '1ºSgt PM Fão', 'periodo': 2, 'duracao': 2},
            {'materia': 'Ordem Unida', 'instrutor': 'Sgt PM Bastos', 'periodo': 6, 'duracao': 1},
        ],
        'quarta': [
             {'materia': 'Gestão e Supervisão pela Qualidade do Serviço', 'instrutor': '1ºSgt PM Fão', 'periodo': 3, 'duracao': 1},
        ],
        'quinta': [
             {'materia': 'Policiamento Ostensivo', 'instrutor': 'Cap PM Silva', 'periodo': 5, 'duracao': 3},
        ],
        'sexta': [],
        # Dados de exemplo para o fim de semana
        'sabado': [
            {'materia': 'Atividade Física Militar', 'instrutor': 'Sgt PM Torres', 'periodo': 1, 'duracao': 4},
        ],
        'domingo': [] # Domingo sem aulas neste exemplo
    }

    # A matriz agora tem 7 colunas para os 7 dias da semana
    horario_matrix = [[None for _ in range(7)] for _ in range(15)]
    dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']

    for dia_idx, dia in enumerate(dias):
        if dia in schedule_raw:
            for aula in schedule_raw[dia]:
                periodo_idx = aula['periodo'] - 1
                if 0 <= periodo_idx < 15:
                    horario_matrix[periodo_idx][dia_idx] = aula
                    for i in range(1, aula['duracao']):
                        if periodo_idx + i < 15:
                           horario_matrix[periodo_idx + i][dia_idx] = 'SKIP'
    
    return render_template('quadro_horario.html', horario_matrix=horario_matrix)