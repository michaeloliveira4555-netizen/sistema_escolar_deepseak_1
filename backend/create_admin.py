# backend/create_admin.py
import os
import sys

# Adiciona o diretório pai (a raiz do projeto) ao caminho de busca do Python
# Isso resolve o erro de importação.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from app import create_app, db
from models.user import User
from werkzeug.security import generate_password_hash # type: ignore

# Cria e inicializa o aplicativo Flask
app = create_app()

def create_admin_user():
    """Cria o usuário administrador se ele não existir."""
    with app.app_context():
        print("Verificando se o usuário admin já existe...")
        
        # Tenta encontrar o usuário 'admin'
        admin_user = db.session.execute(db.select(User).filter_by(username='admin')).scalar_one_or_none()

        if not admin_user:
            print("Usuário 'admin' não encontrado. Criando agora...")
            
            # Crie o novo usuário
            admin_user = User(
                username='admin',
                email='admin@esfas.com.br',
                password_hash=generate_password_hash('@Nk*BC6GAJi8RrT'),
                role='admin'
            )
            
            # Adiciona e salva o usuário no banco de dados
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário administrador 'admin' criado com sucesso!")
            print("A senha é: @Nk*BC6GAJi8RrT")
        else:
            print("O usuário 'admin' já existe no banco de dados. Nenhuma ação necessária.")

if __name__ == '__main__':
    create_admin_user()