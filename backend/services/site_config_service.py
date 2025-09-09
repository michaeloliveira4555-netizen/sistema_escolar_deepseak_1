from ..models.database import db
from ..models.site_config import SiteConfig
from sqlalchemy import select

class SiteConfigService:
    
    @staticmethod
    def get_config(key: str, default_value: str = None):
        """Pega uma configuração do site"""
        config = db.session.execute(
            select(SiteConfig).where(SiteConfig.config_key == key)
        ).scalar_one_or_none()
        
        return config.config_value if config else default_value
    
    @staticmethod
    def set_config(key: str, value: str, config_type: str = 'text', 
                   description: str = None, category: str = 'general', 
                   updated_by: int = None):
        """Define uma configuração do site"""
        config = db.session.execute(
            select(SiteConfig).where(SiteConfig.config_key == key)
        ).scalar_one_or_none()
        
        if config:
            config.config_value = value
            config.config_type = config_type
            config.description = description
            config.category = category
            config.updated_by = updated_by
        else:
            config = SiteConfig(
                config_key=key,
                config_value=value,
                config_type=config_type,
                description=description,
                category=category,
                updated_by=updated_by
            )
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def get_all_configs():
        """Pega todas as configurações"""
        return db.session.execute(select(SiteConfig)).scalars().all()
    
    @staticmethod
    def get_configs_by_category(category: str):
        """Pega configurações por categoria"""
        return db.session.execute(
            select(SiteConfig).where(SiteConfig.category == category)
        ).scalars().all()
    
    @staticmethod
    def init_default_configs():
        """Inicializa configurações padrão"""
        defaults = [
            # Configurações gerais
            ('site_background', '', 'image', 'Imagem de fundo do site', 'general'),
            ('site_logo', '', 'image', 'Logo principal do site', 'general'),
            ('primary_color', '#3b82f6', 'color', 'Cor primária do site', 'general'),
            ('secondary_color', '#1a232c', 'color', 'Cor secundária do site', 'general'),
            ('navbar_background_image', '', 'image', 'Imagem de fundo da barra de navegação', 'general'),
            
            # Ícones do dashboard
            ('dashboard_card_alunos_icon', '👥', 'text', 'Ícone do card Alunos', 'dashboard'),
            ('dashboard_card_instrutores_icon', '🎓', 'text', 'Ícone do card Instrutores', 'dashboard'),
            ('dashboard_card_disciplinas_icon', '📚', 'text', 'Ícone do card Disciplinas', 'dashboard'),
            ('dashboard_card_historico_icon', '📊', 'text', 'Ícone do card Histórico', 'dashboard'),
            ('dashboard_card_assets_icon', '🎨', 'text', 'Ícone do card Assets', 'dashboard'),
            
            # Imagens de fundo dos cards
            ('dashboard_card_alunos_bg', '', 'image', 'Imagem de fundo do card Alunos', 'dashboard'),
            ('dashboard_card_instrutores_bg', '', 'image', 'Imagem de fundo do card Instrutores', 'dashboard'),
            ('dashboard_card_disciplinas_bg', '', 'image', 'Imagem de fundo do card Disciplinas', 'dashboard'),
            ('dashboard_card_historico_bg', '', 'image', 'Imagem de fundo do card Histórico', 'dashboard'),
            ('dashboard_card_assets_bg', '', 'image', 'Imagem de fundo do card Assets', 'dashboard'),
            ('dashboard_card_customizer_bg', '', 'image', 'Imagem de fundo do card Customizar', 'dashboard'),
            ('dashboard_header_bg', '', 'image', 'Imagem de fundo do cabeçalho do dashboard', 'dashboard'),
            
            # Sidebar
            ('sidebar_logo', '', 'image', 'Logo da sidebar', 'sidebar'),

            # Ícones das Turmas (NOVA SEÇÃO)
            ('turma_1_icon', '', 'image', 'Ícone da Turma 1', 'turmas'),
            ('turma_2_icon', '', 'image', 'Ícone da Turma 2', 'turmas'),
            ('turma_3_icon', '', 'image', 'Ícone da Turma 3', 'turmas'),
            ('turma_4_icon', '', 'image', 'Ícone da Turma 4', 'turmas'),
            ('turma_5_icon', '', 'image', 'Ícone da Turma 5', 'turmas'),
            ('turma_6_icon', '', 'image', 'Ícone da Turma 6', 'turmas'),
            ('turma_7_icon', '', 'image', 'Ícone da Turma 7', 'turmas'),
            ('turma_8_icon', '', 'image', 'Ícone da Turma 8', 'turmas'),
        ]
        
        for key, value, config_type, description, category in defaults:
            existing = db.session.execute(
                select(SiteConfig).where(SiteConfig.config_key == key)
            ).scalar_one_or_none()
            
            if not existing:
                config = SiteConfig(
                    config_key=key,
                    config_value=value,
                    config_type=config_type,
                    description=description,
                    category=category
                )
                db.session.add(config)
        
        db.session.commit()