import os
from flask import Flask
# Removido: from flask_login import LoginManager
# Removido: from flask_migrate import Migrate

from .config import Config
from .models import User # Importamos User a partir do __init__.py dos models
from .extensions import db, migrate, login_manager # IMPORTANTE: Importamos daqui

# Importando os controllers
from .controllers.main_controller import main_bp
from .controllers.auth_controller import auth_bp
from .controllers.aluno_controller import aluno_bp
from .controllers.instrutor_controller import instrutor_bp
from .controllers.disciplina_controller import disciplina_bp
from .controllers.historico_controller import historico_bp

def create_app(config_class=Config):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # IMPORTANTE: Inicializamos as extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Registrando os blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(instrutor_bp, url_prefix='/instrutor')
    app.register_blueprint(disciplina_bp, url_prefix='/disciplina')
    app.register_blueprint(historico_bp, url_prefix='/historico')

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    return app

app = create_app()

# ... (seu comando create-admin continua igual) ...
@app.cli.command("create-admin")
def create_admin():
    # ... (código do create-admin) ...
    pass # Adicione o código completo aqui

if __name__ == '__main__':
    app.run(debug=True)