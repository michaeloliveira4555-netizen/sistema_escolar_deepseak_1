from flask import Blueprint, render_template, request, flash, Response
from flask_login import login_required
from weasyprint import HTML
from datetime import datetime
from ..services.relatorio_service import RelatorioService
from utils.decorators import admin_or_programmer_required
import locale

# Configura o locale para Português do Brasil para traduzir o mês
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        print("Locale pt_BR não pôde ser configurado.")


relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@relatorios_bp.route('/')
@login_required
@admin_or_programmer_required
def index():
    return render_template('relatorios/index.html')

@relatorios_bp.route('/horas_aula', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def horas_aula_instrutor():
    if request.method == 'POST':
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        chefe_ensino_nome = request.form.get('chefe_ensino_nome', '')
        chefe_ensino_cargo = request.form.get('chefe_ensino_cargo', 'Chefe da Seção de Ensino')
        comandante_nome = request.form.get('comandante_nome', '')
        comandante_cargo = request.form.get('comandante_cargo', 'Comandante da EsFAS-SM')
        action = request.form.get('action')

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
            return render_template('relatorios/horas_aula_form.html')

        dados_relatorio = RelatorioService.get_horas_aula_por_instrutor(data_inicio, data_fim)

        data_geracao = datetime.now().strftime("%d de %B de %Y")
        cidade_estado = "Santa Maria - RS"

        rendered_html = render_template('relatorios/pdf_template.html',
                                        dados=dados_relatorio,
                                        data_inicio=data_inicio,
                                        data_fim=data_fim,
                                        chefe_ensino_nome=chefe_ensino_nome,
                                        chefe_ensino_cargo=chefe_ensino_cargo,
                                        comandante_nome=comandante_nome,
                                        comandante_cargo=comandante_cargo,
                                        data_geracao=data_geracao,
                                        cidade_estado=cidade_estado)

        if action == 'preview':
            return rendered_html

        if action == 'download':
            # A orientação da página agora é controlada diretamente no template
            pdf = HTML(string=rendered_html).write_pdf()
            return Response(pdf, mimetype='application/pdf', headers={
                'Content-Disposition': 'attachment; filename=relatorio_horas_aula.pdf'
            })

    return render_template('relatorios/horas_aula_form.html')