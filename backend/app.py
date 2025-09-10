import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from backend.config import Config
from backend.models.database import db
from backend.models.user import User
# Importações dos novos modelos para que o Flask-Migrate os reconheça
from backend.models.semana import Semana
from backend.models.horario import Horario
from backend.models.disciplina_turma import DisciplinaTurma
from backend.models.turma import Turma
from backend.models.turma_cargo import TurmaCargo

def create_app(config_class=Config):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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

        print("Criando o usuário administrador 'admin'...")
        new_admin = User(
            id_func='ADMIN',
            username='admin',
            email='admin@escola.com.br',
            role='admin',
            is_active=True
        )
        new_admin.set_password('@Nk*BC6GAJi8RrT')

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

        print("Criando o usuário programador...")
        new_programmer = User(
            id_func='PROG001',
            username='programador',
            email='dev@escola.com.br',
            role='programador',
            is_active=True
        )
        new_programmer.set_password('DevPass@2025')

        db.session.add(new_programmer)
        db.session.commit()
        
        print("Usuário programador criado com sucesso!")
        print("Login: programador")
        print("Senha: DevPass@2025")

@app.cli.command("seed-disciplinas")
def seed_disciplinas():
    """Adiciona a lista de disciplinas padrão ao banco de dados."""
    from backend.models.disciplina import Disciplina

    lista_disciplinas = [
        "Educação Física", "Sistemas de Correição: Atribuição do Escrivão PJM",
        "A Transversalidade do D. Penal e Processual Penal no Atnd. De Oc.",
        "Legislação Especial Aplicada a Função Policial Militar", "Policiamento de Trânsito Aplicado a Função",
        "Gestão e Supervisão pela Qualidade do Serviço", "Sistemas Informatizados da BM e SSPO",
        "Saúde Mental do Policial Militar e Psicologia da Ativ. Pol.", "Direito Administrativo Aplicado a função Policial Militar",
        "Gerenciamento de Crise e Desastres", "Ordem Unida", "AMT I", "AMT II",
        "Atendimento Pré-Hospitalar Tático", "A disposição do C Al /S Ens"
    ]
    print("Verificando e adicionando disciplinas...")
    count = 0
    for nome_materia in lista_disciplinas:
        disciplina_existe = db.session.execute(db.select(Disciplina).filter_by(materia=nome_materia)).scalar_one_or_none()
        if not disciplina_existe:
            nova_disciplina = Disciplina(materia=nome_materia, carga_horaria_prevista=0)
            db.session.add(nova_disciplina)
            count += 1
    if count > 0:
        db.session.commit()
        print(f"{count} nova(s) disciplina(s) adicionada(s) com sucesso!")
    else:
        print("Todas as disciplinas padrão já existem no banco de dados.")

if __name__ == '__main__':
    app.run(debug=True)