import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from backend.config import Config
from backend.models.database import db
from backend.models.user import User

# Importa todos os seus Blueprints (rotas)
from backend.controllers.auth_controller import auth_bp
from backend.controllers.aluno_controller import aluno_bp
from backend.controllers.instrutor_controller import instrutor_bp
from backend.controllers.disciplina_controller import disciplina_bp
from backend.controllers.historico_controller import historico_bp
from backend.controllers.main_controller import main_bp

def create_app(config_class=Config):
    # Obtém o caminho absoluto para o diretório raiz do projeto
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Inicializa as extensões
    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # type: ignore
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Registra os Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(instrutor_bp, url_prefix='/instrutor')
    app.register_blueprint(disciplina_bp, url_prefix='/disciplina')
    app.register_blueprint(historico_bp, url_prefix='/historico')
    app.register_blueprint(main_bp) 

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    return app

# Cria a instância da aplicação
app = create_app()

# --- ESTE É O COMANDO DE ADMINISTRAÇÃO ---
# Ele só roda quando você digita "flask create-admin" no terminal
@app.cli.command("create-admin")
def create_admin():
    """Cria o usuário administrador inicial."""
    with app.app_context():
        admin_user = db.session.execute(db.select(User).filter_by(username='admin')).scalar_one_or_none()
        
        if admin_user:
            print("O usuário 'admin' já existe.")
            return

        print("Criando o usuário administrador 'admin'...")
        new_admin = User(
            matricula='ADMIN',      # ADICIONADO: Matrícula obrigatória para o admin
            username='admin',
            email='admin@escola.com.br',
            role='admin',
            is_active=True          # ADICIONADO: Ativa a conta do admin imediatamente
)
        # Usa o método correto para definir a senha
        new_admin.set_password('@Nk*BC6GAJi8RrT')

        db.session.add(new_admin)
        db.session.commit()
        
        print("Usuário administrador 'admin' criado com sucesso!")

# --- ESTA É A FORMA CORRETA DE INICIAR O SERVIDOR ---
# Apenas inicia a aplicação, sem lógicas extras.
if __name__ == '__main__':
    app.run(debug=True)