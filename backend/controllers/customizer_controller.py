from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from ..extensions import db
from ..models.image_asset import ImageAsset
from ..models.site_config import SiteConfig
from ..services.site_config_service import SiteConfigService
from utils.decorators import admin_required

customizer_bp = Blueprint('customizer', __name__, url_prefix='/customizer')

@customizer_bp.route('/')
@login_required
@admin_required
def index():
    """Painel principal de customização"""
    # Inicializa configurações padrão se não existirem
    SiteConfigService.init_default_configs()
    
    configs = SiteConfigService.get_all_configs()
    assets = db.session.query(ImageAsset).filter_by(is_active=True).all()
    
    # Organiza configs por categoria
    configs_by_category = {}
    for config in configs:
        if config.category not in configs_by_category:
            configs_by_category[config.category] = []
        configs_by_category[config.category].append(config)
    
    return render_template('customizer/index.html', 
                         configs_by_category=configs_by_category, 
                         assets=assets)

@customizer_bp.route('/update', methods=['POST'])
@login_required
@admin_required
def update_config():
    """Atualiza uma configuração"""
    config_key = request.form.get('config_key')
    config_value = request.form.get('config_value')
    config_type = request.form.get('config_type', 'text')
    
    if not config_key:
        return jsonify({'success': False, 'message': 'Chave de configuração não fornecida'})
    
    try:
        SiteConfigService.set_config(
            key=config_key,
            value=config_value,
            config_type=config_type,
            updated_by=current_user.id
        )
        
        return jsonify({'success': True, 'message': 'Configuração atualizada com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@customizer_bp.route('/preview')
@login_required
@admin_required
def preview():
    """Preview das configurações"""
    configs = SiteConfigService.get_all_configs()
    config_dict = {config.config_key: config.config_value for config in configs}
    
    return render_template('customizer/preview.html', configs=config_dict)

@customizer_bp.route('/reset', methods=['POST'])
@login_required
@admin_required
def reset_configs():
    """Reset todas as configurações para padrão"""
    try:
        # Deleta todas as configurações usando o modelo importado
        db.session.query(SiteConfig).delete()
        db.session.commit()
        
        # Reinicializa com padrões
        SiteConfigService.init_default_configs()
        
        flash('Configurações resetadas para o padrão!', 'success')
        return redirect(url_for('customizer.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao resetar configurações: {str(e)}', 'error')
        return redirect(url_for('customizer.index'))

