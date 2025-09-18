from flask import Blueprint, render_template, request, flash, Response
from flask_login import login_required
from datetime import datetime
from ..services.relatorio_service import RelatorioService
from ..services.instrutor_service import InstrutorService
from utils.decorators import admin_or_programmer_required
from ..services.site_config_service import SiteConfigService
import locale
import requests
import io

# Configura o locale para Português do Brasil para traduzir o mês
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        print("Locale pt_BR não pôde ser configurado.")

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

# URL da API do WeasyPrint (container Docker)
WEASYPRINT_API_URL = "http://localhost:5001"

def gerar_pdf_com_api(html_content):
    """Função para gerar PDF usando a API do WeasyPrint"""
    try:
        response = requests.post(
            f"{WEASYPRINT_API_URL}/pdf",
            json={'html': html_content},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Erro na API WeasyPrint: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        raise Exception("Serviço de PDF não disponível. Verifique se o container weasyprint-api está rodando.")
    except requests.exceptions.Timeout:
        raise Exception("Timeout ao conectar com o serviço de PDF.")
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF: {str(e)}")

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
        chefe_ensino_nome = request.form.get('chefe_ensino_nome', '')
        comandante_nome = request.form.get('comandante_nome', '')
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

        data_geracao = datetime.now().strftime("%d de %B de %Y")
        
        # Usar configurações do SiteConfigService
        chefe_ensino_cargo = SiteConfigService.get_config('report_chefe_ensino_cargo', 'Chefe da Seção de Ensino')
        comandante_cargo = SiteConfigService.get_config('report_comandante_cargo', 'Comandante da EsFAS-SM')
        cidade_estado = SiteConfigService.get_config('report_cidade_estado', 'Santa Maria - RS')

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

            try:
                # Usa a API do WeasyPrint em vez da importação direta
                pdf_content = gerar_pdf_com_api(rendered_html)
                
                return Response(
                    pdf_content,
                    mimetype='application/pdf',
                    headers={
                        'Content-Disposition': 'attachment; filename=relatorio_horas_aula.pdf'
                    }
                )
            except Exception as e:
                flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
                return render_template('relatorios/horas_aula_form.html')

    return render_template('relatorios/horas_aula_form.html', 
                           tipo_relatorio=report_type.replace("_", " ").title(), 
                           todos_instrutores=todos_instrutores)