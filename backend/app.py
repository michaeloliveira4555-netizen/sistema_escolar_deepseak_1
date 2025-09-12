import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel

from backend.config import Config
from backend.models.database import db
from backend.models.user import User
# Importações dos novos modelos para que o Flask-Migra os reconheça
from backend.models.semana import Semana
from backend.models.horario import Horario
from backend.models.disciplina_turma import DisciplinaTurma
from backend.models.turma import Turma
from backend.models.turma_cargo import TurmaCargo
from backend.services.asset_service import AssetService

# Crie o limiter como uma variável global
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    babel = Babel(app)
    db.init_app(app)
    Migrate(app, db)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Configure o limiter com a app
    limiter.init_app(app)
    limiter.default_limits = ["200 per day", "50 per hour"]
    limiter.storage_uri = "redis://localhost:6379"  
    limiter.storage_options = {"socket_connect_timeout": 30}
    limiter.strategy = "fixed-window"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Initialize AssetService UPLOAD_FOLDER
    AssetService.initialize_upload_folder(app)

    # Importa os Blueprints
    from backend.controllers.auth_controller import auth_bp
    from backend.controllers.aluno_controller import aluno_bp
    from backend.controllers.instrutor_controller import instrutor_bp
    from backend.controllers.disciplina_controller import disciplina_bp
    from backend.controllers.historico_controller import historico_bp
    from backend.controllers.main_controller import main_bp
    from backend.controllers.assets_controller import assets_bp
    from backend.controllers.customizer_controller import customizer_bp
    from backend.controllers.horario_controller import horario_bp
    from backend.controllers.semana_controller import semana_bp
    from backend.controllers.turma_controller import turma_bp
    from backend.controllers.vinculo_controller import vinculo_bp
    from backend.controllers.user_controller import user_bp
    from backend.controllers.relatorios_controller import relatorios_bp # <-- 1. IMPORTAR O NOVO BLUEPRINT

    # Registra os Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(instrutor_bp, url_prefix='/instrutor')
    app.register_blueprint(disciplina_bp, url_prefix='/disciplina')
    app.register_blueprint(historico_bp, url_prefix='/historico')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(customizer_bp, url_prefix='/customizer')
    app.register_blueprint(main_bp)
    app.register_blueprint(horario_bp)
    app.register_blueprint(semana_bp, url_prefix='/semana')
    app.register_blueprint(turma_bp, url_prefix='/turma')
    app.register_blueprint(vinculo_bp, url_prefix='/vinculos')
    app.register_blueprint(user_bp)
    app.register_blueprint(relatorios_bp) # <-- 2. REGISTRAR O NOVO BLUEPRINT

    # Context processor para configurações do site
    @app.context_processor
    def inject_site_configs():
        from backend.services.site_config_service import SiteConfigService
        configs = SiteConfigService.get_all_configs()
        config_dict = {config.config_key: config.config_value for config in configs}
        return dict(site_config=config_dict)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app

# Cria a instância da aplicação
app = create_app()

# Comando para criar admin
@app.cli.command("create-admin")
def create_admin():
    with app.app_context():
        admin_user = db.session.execute(db.select(User).filter_by(id_func='ADMIN')).scalar_one_or_none()

        if admin_user:
            print("O usuário 'admin' já existe.")
            return

        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            print("A variável de ambiente ADMIN_PASSWORD não está definida.")
            print("Por favor, defina a senha antes de criar o administrador.")
            return

        print("Criando o usuário administrador 'admin'...")
        new_admin = User(
            id_func='ADMIN',
            username='admin',
            email='admin@escola.com.br',
            role='admin',
            is_active=True
        )
        new_admin.set_password(admin_password)

        db.session.add(new_admin)
        db.session.commit()

        print("Usuário administrador 'admin' criado com sucesso!")

# Comando para criar programador
@app.cli.command("create-programmer")
def create_programmer():
    with app.app_context():
        prog_user = db.session.execute(db.select(User).filter_by(id_func='PROG001')).scalar_one_or_none()

        if prog_user:
            print("O usuário 'programador' já existe.")
            return

        prog_password = os.environ.get('PROGRAMMER_PASSWORD')
        if not prog_password:
            print("A variável de ambiente PROGRAMMER_PASSWORD não está definida.")
            print("Por favor, defina a senha antes de criar o programador.")
            return

        print("Criando o usuário programador...")
        new_programmer = User(
            id_func='PROG001',
            username='programador',
            email='dev@escola.com.br',
            role='programador',
            is_active=True
        )
        new_programmer.set_password(prog_password)

        db.session.add(new_programmer)
        db.session.commit()

        print("Usuário programador criado com sucesso!")


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')