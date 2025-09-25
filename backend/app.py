# backend/app.py

import os
import time  # <-- ADICIONE ESTA LINHA
from flask import Flask, render_template
import click
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

from backend.extensions import limiter
from backend.config import Config
from backend.models.database import db
from backend.models.user import User
# Importações de todos os modelos para que o Flask-Migrate os reconheça
from backend.models.aluno import Aluno
from backend.models.disciplina import Disciplina
from backend.models.disciplina_turma import DisciplinaTurma
from backend.models.historico import HistoricoAluno
from backend.models.historico_disciplina import HistoricoDisciplina
from backend.models.horario import Horario
from backend.models.image_asset import ImageAsset
from backend.models.instrutor import Instrutor
from backend.models.password_reset_token import PasswordResetToken
from backend.models.school import School
from backend.models.semana import Semana
from backend.models.site_config import SiteConfig
from backend.models.turma import Turma
from backend.models.turma_cargo import TurmaCargo
from backend.models.user_school import UserSchool
from backend.services.asset_service import AssetService
# IMPORTAÇÃO DOS NOVOS MODELOS DE QUESTIONÁRIO
from backend.models.questionario import Questionario
from backend.models.pergunta import Pergunta
from backend.models.opcao_resposta import OpcaoResposta
from backend.models.resposta import Resposta


def create_app(config_class=Config):
    """
    Fábrica de aplicação: cria e configura a instância do Flask.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Executa a verificação da config (importante para produção)
    config_class.init_app(app)

    # Inicializa as extensões com a app
    db.init_app(app)
    Migrate(app, db)
    CSRFProtect(app)
    limiter.init_app(app)
    Babel(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Um contexto é necessário para registrar blueprints e outras configurações
    with app.app_context():
        AssetService.initialize_upload_folder(app)
        register_blueprints(app)
        register_handlers_and_processors(app)
        
    register_cli_commands(app)
    return app

def register_blueprints(app):
    """Importa e registra os blueprints na aplicação."""
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
    from backend.controllers.relatorios_controller import relatorios_bp
    from backend.controllers.super_admin_controller import super_admin_bp
    from backend.controllers.admin_controller import admin_escola_bp
    # IMPORTAÇÃO DO NOVO BLUEPRINT DE QUESTIONÁRIO
    from backend.controllers.questionario_controller import questionario_bp


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(instrutor_bp, url_prefix='/instrutor')
    app.register_blueprint(disciplina_bp, url_prefix='/disciplina')
    app.register_blueprint(historico_bp, url_prefix='/historico')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(customizer_bp, url_prefix='/customizer')
    app.register_blueprint(main_bp)
    app.register_blueprint(horario_bp, url_prefix='/horario')
    app.register_blueprint(semana_bp, url_prefix='/semana')
    app.register_blueprint(turma_bp, url_prefix='/turma')
    app.register_blueprint(vinculo_bp, url_prefix='/vinculos')
    app.register_blueprint(user_bp, url_prefix='/usuario')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(super_admin_bp, url_prefix='/super-admin')
    app.register_blueprint(admin_escola_bp, url_prefix='/admin-escola')
    # REGISTO DO NOVO BLUEPRINT DE QUESTIONÁRIO
    app.register_blueprint(questionario_bp, url_prefix='/questionario')

def register_handlers_and_processors(app):
    """Registra hooks, context processors e error handlers."""

    # --- ADICIONE ESTA NOVA FUNÇÃO AQUI ---
    @app.context_processor
    def inject_cache_buster():
        """Adiciona um número aleatório ao contexto para evitar o cache de CSS/JS."""
        return dict(cache_buster=int(time.time()))
    # --- FIM DA NOVA FUNÇÃO ---

    @app.context_processor
    def inject_site_configs():
        from backend.services.site_config_service import SiteConfigService
        if app.config.get("TESTING", False):
            SiteConfigService.init_default_configs()
        configs = SiteConfigService.get_all_configs()
        return dict(site_config={c.config_key: c.config_value for c in configs})

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

def register_cli_commands(app):
    """Registra os comandos de linha de comando."""
    @app.cli.command("create-super-admin")
    def create_super_admin():
        with app.app_context():
            super_admin_password = os.environ.get('SUPER_ADMIN_PASSWORD')
            if not super_admin_password:
                print("A variável de ambiente SUPER_ADMIN_PASSWORD não está definida.")
                return
            user = db.session.execute(db.select(User).filter_by(username='super_admin')).scalar_one_or_none()
            if user:
                print("Usuário 'super_admin' já existe. Atualizando senha e ativando...")
                user.is_active = True
                user.set_password(super_admin_password)
            else:
                print("Criando o usuário super administrador 'super_admin'...")
                user = User(
                    id_func='SUPER_ADMIN', 
                    username='super_admin', 
                    email='super_admin@escola.com.br', 
                    role='super_admin', 
                    is_active=True
                )
                user.set_password(super_admin_password)
                db.session.add(user)
            db.session.commit()
            print("Comando executado com sucesso!")

    @app.cli.command("create-programmer")
    def create_programmer():
        with app.app_context():
            prog_password = os.environ.get('PROGRAMMER_PASSWORD')
            if not prog_password:
                print("A variável de ambiente PROGRAMMER_PASSWORD não está definida.")
                return
            user = db.session.execute(db.select(User).filter_by(id_func='PROG001')).scalar_one_or_none()
            if user:
                print("O usuário 'programador' já existe.")
            else:
                print("Criando o usuário programador...")
                user = User(
                    id_func='PROG001', 
                    username='programador', 
                    email='dev@escola.com.br', 
                    role='programador', 
                    is_active=True
                )
                user.set_password(prog_password)
                db.session.add(user)
            db.session.commit()
            print("Usuário programador criado com sucesso!")

    @app.cli.command("fix-role")
    @click.argument("id_func")
    @click.argument("new_role")
    def fix_role_command(id_func, new_role):
        """Atualiza a função (role) de um usuário. Ex: flask fix-role 123456 aluno"""
        from scripts.fix_user_role import fix_user_role_for_cli
        fix_user_role_for_cli(id_func, new_role)
        print("Comando executado.")


# Este bloco só é executado quando o arquivo é chamado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
