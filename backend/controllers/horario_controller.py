from flask import Blueprint, render_template
from flask_login import login_required
from utils.decorators import admin_or_programmer_required

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

@horario_bp.route('/')
@login_required
@admin_or_programmer_required
def index():
    """Página principal do Quadro Horário."""
    return render_template('quadro_horario.html')