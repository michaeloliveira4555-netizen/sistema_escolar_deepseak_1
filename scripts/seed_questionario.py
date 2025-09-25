import sys
import os
from dotenv import load_dotenv

# Adiciona o diretório raiz do projeto ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.models.database import db
from backend.models.questionario import Questionario
from backend.models.pergunta import Pergunta
from backend.models.opcao_resposta import OpcaoResposta

def seed_questionario_for_cli():
    """
    Cria um questionário de exemplo com perguntas e opções de resposta.
    """
    print("Iniciando a criação do questionário de exemplo...")

    try:
        # Verifica se o questionário já existe para não duplicar
        existing_questionario = db.session.query(Questionario).filter_by(titulo="Pesquisa de Satisfação - CTSP").first()
        if existing_questionario:
            print("O questionário de exemplo já existe. Nenhuma ação foi tomada.")
            return

        # 1. Cria o Questionário Principal
        novo_questionario = Questionario(titulo="Pesquisa de Satisfação - CTSP")
        db.session.add(novo_questionario)
        db.session.flush()  # Para obter o ID antes do commit

        print(f"  - Questionário '{novo_questionario.titulo}' criado.")

        # 2. Define a estrutura de Perguntas e Opções
        perguntas_e_opcoes = [
            {
                "texto": "Qual o seu nível de satisfação geral com o curso?",
                "opcoes": ["Muito Satisfeito", "Satisfeito", "Neutro", "Insatisfeito", "Muito Insatisfeito"]
            },
            {
                "texto": "Como você avalia a qualidade do material didático fornecido?",
                "opcoes": ["Excelente", "Bom", "Regular", "Ruim", "Péssimo"]
            },
            {
                "texto": "A didática dos instrutores foi clara e eficiente?",
                "opcoes": ["Sim, na maioria das vezes", "Sim, algumas vezes", "Não, raramente", "Não, nunca"]
            },
            {
                "texto": "As instalações da escola (salas de aula, alojamentos) atenderam às suas necessidades?",
                "opcoes": ["Sim, completamente", "Parcialmente", "Não, foram insuficientes"]
            },
            {
                "texto": "Você recomendaria este curso para outros colegas?",
                "opcoes": ["Com certeza", "Provavelmente sim", "Talvez", "Provavelmente não", "Com certeza não"]
            }
        ]

        # 3. Itera e cria as Perguntas e Opções no banco
        for item in perguntas_e_opcoes:
            pergunta = Pergunta(texto=item["texto"], questionario_id=novo_questionario.id)
            db.session.add(pergunta)
            db.session.flush() # Para obter o ID da pergunta
            print(f"    - Pergunta criada: '{item['texto'][:30]}...'")

            for opt_texto in item["opcoes"]:
                opcao = OpcaoResposta(texto=opt_texto, pergunta_id=pergunta.id)
                db.session.add(opcao)

        db.session.commit()
        print("\nSucesso! Questionário de exemplo criado e salvo no banco de dados.")

    except Exception as e:
        db.session.rollback()
        print(f"\nOcorreu um erro ao tentar criar o questionário: {e}")
