from flask import Blueprint, render_template, request, flash, Response
from flask_login import login_required
from datetime import datetime
from ..services.relatorio_service import RelatorioService
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
    return render_template('relatorios/index.html')

@relatorios_bp.route('/horas_aula', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def horas_aula_instrutor():
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
            return render_template('relatorios/horas_aula_form.html')

        dados_relatorio = RelatorioService.get_horas_aula_por_instrutor(data_inicio, data_fim)

        data_geracao = datetime.now().strftime("%d de %B de %Y")
        
        # Usar configurações do SiteConfigService
        chefe_ensino_cargo = SiteConfigService.get_config('report_chefe_ensino_cargo', 'Chefe da Seção de Ensino')
        comandante_cargo = SiteConfigService.get_config('report_comandante_cargo', 'Comandante da EsFAS-SM')
        cidade_estado = SiteConfigService.get_config('report_cidade_estado', 'Santa Maria - RS')

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

    return render_template('relatorios/horas_aula_form.html')