from flask import Blueprint, render_template, request, flash, Response
from flask_login import login_required
from weasyprint import HTML
from datetime import datetime
from ..services.relatorio_service import RelatorioService
from ..services.instrutor_service import InstrutorService
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
    """Página que exibe os tipos de relatório disponíveis."""
    return render_template('relatorios/index.html')

@relatorios_bp.route('/gerar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def gerar_relatorio_horas_aula():
    """Formulário e lógica para gerar os relatórios de horas-aula."""
    
    report_type = request.args.get('tipo', 'mensal')
    todos_instrutores = None

    if report_type == 'por_instrutor':
        todos_instrutores = InstrutorService.get_all_instrutores()

    if request.method == 'POST':
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        
        curso_nome = request.form.get('curso_nome', '')
        comandante_nome = request.form.get('comandante_nome', '')
        auxiliar_nome = request.form.get('auxiliar_nome', '')
        
        action = request.form.get('action')

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
            return render_template('relatorios/horas_aula_form.html', tipo_relatorio=report_type.replace("_", " ").title(), todos_instrutores=todos_instrutores)

        is_rr_filter = report_type == 'efetivo_rr'
        instrutor_ids_filter = None
        if report_type == 'por_instrutor':
            instrutor_ids_filter = [int(id) for id in request.form.getlist('instrutor_ids')]
            if not instrutor_ids_filter:
                flash('Por favor, selecione pelo menos um instrutor para este tipo de relatório.', 'warning')
                return render_template('relatorios/horas_aula_form.html', tipo_relatorio=report_type.replace("_", " ").title(), todos_instrutores=todos_instrutores)

        dados_relatorio = RelatorioService.get_horas_aula_por_instrutor(
            data_inicio, data_fim, is_rr_filter, instrutor_ids_filter
        )

        # String de Mês e Ano formatada corretamente
        nome_mes_ano = data_inicio.strftime("%B de %Y").capitalize()
        
        titulo_curso = f"NOME DO CURSO: {curso_nome}"
        if report_type == 'efetivo_rr':
            titulo_curso += " (EFETIVO RR)"
        
        rendered_html = render_template('relatorios/pdf_template.html',
                                        dados=dados_relatorio,
                                        data_inicio=data_inicio,
                                        data_fim=data_fim,
                                        titulo_curso=titulo_curso,
                                        nome_mes_ano=nome_mes_ano, # Variável atualizada
                                        comandante_nome=comandante_nome,
                                        auxiliar_nome=auxiliar_nome,
                                        valor_hora_aula=55.19)

        if action == 'preview':
            return rendered_html

        if action == 'download':
            pdf = HTML(string=rendered_html).write_pdf()
            return Response(pdf, mimetype='application/pdf', headers={
                'Content-Disposition': f'attachment; filename=relatorio_{report_type}.pdf'
            })

    return render_template('relatorios/horas_aula_form.html', 
                           tipo_relatorio=report_type.replace("_", " ").title(), 
                           todos_instrutores=todos_instrutores)