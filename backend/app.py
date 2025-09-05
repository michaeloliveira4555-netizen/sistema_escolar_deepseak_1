import os
from flask import Flask

# Importa as configurações
from .config import Config
# Importa os modelos através do __init__.py para um acesso mais limpo
from .models import User
# Importa as instâncias das extensões a partir do arquivo centralizado
from .extensions import db, migrate, login_manager

# Importando todos os controllers (Blueprints)
# CORREÇÃO APLICADA AQUI: Todas as importações agora são relativas (com ponto)
from .controllers.main_controller import main_bp
from .controllers.auth_controller import auth_bp
from .controllers.aluno_controller import aluno_bp
from .controllers.instrutor_controller import instrutor_bp
from .controllers.disciplina_controller import disciplina_bp
from .controllers.historico_controller import historico_bp
from .controllers.admin_controller import admin_bp
from .controllers.assets_controller import assets_bp
from .controllers.customizer_controller import customizer_bp

def create_app(config_class=Config):
    """
    Cria e configura a instância da aplicação Flask (Application Factory).
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Inicializa as extensões com a instância da aplicação
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        # Carrega o usuário a partir do ID da sessão
        return db.session.get(User, int(user_id))

    # Registrando os blueprints na aplicação
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(instrutor_bp, url_prefix='/instrutor')
    app.register_blueprint(disciplina_bp, url_prefix='/disciplina')
    app.register_blueprint(historico_bp, url_prefix='/historico')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(customizer_bp, url_prefix='/customizer')

    # Context processor para injetar configurações do site em todos os templates
    @app.context_processor
    def inject_site_configs():
        from .services.site_config_service import SiteConfigService
        configs = SiteConfigService.get_all_configs()
        config_dict = {config.config_key: config.config_value for config in configs}
        return dict(site_config=config_dict)

    @app.after_request
    def add_header(response):
        # Garante que o navegador não faça cache das páginas
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    return app

# Cria a instância principal da aplicação para ser usada pelo Flask CLI
app = create_app()

# --- Comandos CLI para gerenciamento ---

@app.cli.command("create-admin")
def create_admin():
    """Cria o usuário administrador padrão."""
    with app.app_context():
        admin_user = db.session.execute(db.select(User).filter_by(username='admin')).scalar_one_or_none()
        
        if admin_user:
            print("O usuário 'admin' já existe.")
            return

        print("Criando o usuário administrador 'admin'...")
        new_admin = User(
            matricula='ADMIN001', # Campo obrigatório
            username='admin',
            email='admin@escola.com.br',
            role='admin',
            is_active=True
        )
        new_admin.set_password('@Nk*BC6GAJi8RrT')

        db.session.add(new_admin)
        db.session.commit()
        
        print("Usuário administrador 'admin' criado com sucesso!")
        print("Senha: @Nk*BC6GAJi8RrT")

if __name__ == '__main__':
    app.run(debug=True)

