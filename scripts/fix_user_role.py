# scripts/fix_user_role.py
import sys
import os
from sqlalchemy import select

# Adiciona o diretório raiz do projeto ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import db
from backend.models.user import User

def fix_user_role_for_cli(id_func: str, new_role: str):
    """
    Função chamada pelo comando CLI para atualizar a role de um usuário.
    """
    if new_role not in ['aluno', 'instrutor', 'admin_escola', 'super_admin', 'programador']:
        print(f"Erro: A função '{new_role}' não é válida.")
        return

    print(f"Procurando usuário com ID Funcional: {id_func}...")

    user = db.session.scalar(select(User).where(User.id_func == id_func))

    if not user:
        print(f"Usuário com ID Funcional '{id_func}' não encontrado.")
        return

    old_role = user.role
    if old_role == new_role:
        print(f"O usuário já possui a função '{new_role}'. Nenhuma alteração necessária.")
        return

    print(f"Usuário encontrado: {user.nome_completo or user.username}. Função atual: '{old_role}'.")
    
    try:
        user.role = new_role
        db.session.commit()
        print(f"Sucesso! A função do usuário foi alterada de '{old_role}' para '{new_role}'.")
    except Exception as e:
        db.session.rollback()
        print(f"Ocorreu um erro ao tentar salvar as alterações: {e}")