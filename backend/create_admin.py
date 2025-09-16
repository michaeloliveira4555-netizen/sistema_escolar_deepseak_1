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

def create_super_admin_user():
    """Cria o usuário super administrador se ele não existir."""
    with app.app_context():
        print("Verificando se o usuário super_admin já existe...")
        
        # Tenta encontrar o usuário 'super_admin'
        super_admin_user = db.session.execute(db.select(User).filter_by(username='super_admin')).scalar_one_or_none()

        if not super_admin_user:
            print("Usuário 'super_admin' não encontrado. Criando agora...")
            
            # Crie o novo usuário
            super_admin_user = User(
                id_func='SUPER_ADMIN',
                username='super_admin',
                email='super_admin@esfas.com.br',
                password_hash=generate_password_hash('@Nk*BC6GAJi8RrT'), # Manter a senha padrão por enquanto
                role='super_admin'
            )
            
            # Adiciona e salva o usuário no banco de dados
            db.session.add(super_admin_user)
            db.session.commit()
            print("Usuário super administrador 'super_admin' criado com sucesso!")
            print("A senha é: @Nk*BC6GAJi8RrT")
        else:
            print("O usuário 'super_admin' já existe no banco de dados. Nenhuma ação necessária.")

if __name__ == '__main__':
    create_super_admin_user()