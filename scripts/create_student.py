# scripts/create_student.py

import sys
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do ficheiro .flaskenv
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.flaskenv')
load_dotenv(dotenv_path=dotenv_path)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models.database import db
from backend.models.user import User
from backend.models.aluno import Aluno
from backend.models.user_school import UserSchool
from sqlalchemy import select

# --- DADOS DO NOVO ALUNO ---
ID_FUNC = "4356853"
SENHA = "Niki801028@"
NOME_COMPLETO = "Aluno Teste"
NOME_DE_GUERRA = "Teste"
ESCOLA_ID_PADRAO = 1 # Assumimos que a escola com ID 1 existe
TURMA_ID_PADRAO = 1 # Assumimos que a turma com ID 1 existe
OPM_PADRAO = "Batalhão Padrão"

def criar_aluno():
    """
    Cria um novo utilizador do tipo 'aluno' e o seu perfil correspondente.
    """
    app = create_app()
    with app.app_context():
        # 1. Verificar se o utilizador já existe
        utilizador_existente = db.session.scalar(
            select(User).where(User.id_func == ID_FUNC)
        )
        if utilizador_existente:
            print(f"ERRO: O utilizador com a Id Func '{ID_FUNC}' já existe.")
            return

        print(f"A criar o utilizador '{NOME_COMPLETO}' com a Id Func '{ID_FUNC}'...")

        # 2. Criar a entrada na tabela User
        novo_utilizador = User(
            id_func=ID_FUNC,
            username=ID_FUNC,
            nome_completo=NOME_COMPLETO,
            nome_de_guerra=NOME_DE_GUERRA,
            role='aluno',
            is_active=True
        )
        novo_utilizador.set_password(SENHA)
        db.session.add(novo_utilizador)
        db.session.flush() # Para obter o ID do novo utilizador

        # 3. Criar o perfil do Aluno
        novo_aluno = Aluno(
            user_id=novo_utilizador.id,
            matricula=ID_FUNC, # Usamos a Id Func como matrícula por defeito
            opm=OPM_PADRAO,
            turma_id=TURMA_ID_PADRAO
        )
        db.session.add(novo_aluno)
        
        # 4. Associar o utilizador a uma escola
        associacao_escola = UserSchool(
            user_id=novo_utilizador.id,
            school_id=ESCOLA_ID_PADRAO,
            role='aluno'
        )
        db.session.add(associacao_escola)

        # 5. Guardar tudo na base de dados
        try:
            db.session.commit()
            print("\nSUCESSO!")
            print(f"Conta de aluno criada para '{NOME_COMPLETO}'.")
            print(f"Utilizador: {ID_FUNC}")
            print(f"Senha: {SENHA}")
        except Exception as e:
            db.session.rollback()
            print(f"\nERRO: Ocorreu um erro ao guardar na base de dados: {e}")
            print("Verifique se a escola com ID=1 e a turma com ID=1 existem na sua base de dados.")

if __name__ == '__main__':
    criar_aluno()