import sys
import os
from sqlalchemy import select

# Adiciona o diretório raiz do projeto ao path do Python para permitir importações corretas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models.database import db
from backend.models.turma import Turma
from backend.models.disciplina_turma import DisciplinaTurma

def cleanup_invalid_vinculos():
    """
    Este script limpa a tabela de vínculos (disciplina_turmas), removendo
    quaisquer registros que se refiram a turmas que não existem mais.
    """
    app = create_app()
    with app.app_context():
        print("Iniciando a limpeza de vínculos inválidos...")

        # 1. Obter todos os nomes de turmas válidas que existem na tabela 'turmas'
        turmas_validas_query = select(Turma.nome)
        nomes_turmas_validas = [nome for nome, in db.session.execute(turmas_validas_query).all()]

        if not nomes_turmas_validas:
            print("Nenhuma turma encontrada na tabela 'turmas'. A limpeza não pode continuar.")
            return

        print(f"Turmas válidas encontradas: {', '.join(nomes_turmas_validas)}")

        # 2. Encontrar todos os vínculos que apontam para turmas que NÃO ESTÃO na lista de turmas válidas
        vinculos_invalidos_query = select(DisciplinaTurma).where(
            DisciplinaTurma.pelotao.notin_(nomes_turmas_validas)
        )
        vinculos_para_deletar = db.session.scalars(vinculos_invalidos_query).all()

        if not vinculos_para_deletar:
            print("Nenhum vínculo inválido encontrado. Seu banco de dados está limpo!")
            return

        # 3. Deletar os vínculos inválidos
        print(f"Encontrados {len(vinculos_para_deletar)} vínculos inválidos para serem removidos:")
        for vinculo in vinculos_para_deletar:
            instrutor_info = f"(Instrutor ID: {vinculo.instrutor_id_1})" if vinculo.instrutor_id_1 else "(Sem instrutor)"
            print(f"  - Vínculo ID {vinculo.id}: Turma '{vinculo.pelotao}' (inválida) {instrutor_info}")
            db.session.delete(vinculo)

        # 4. Salvar as alterações no banco de dados
        try:
            db.session.commit()
            print("\nLimpeza concluída com sucesso! Os vínculos inválidos foram removidos.")
        except Exception as e:
            db.session.rollback()
            print(f"\nOcorreu um erro ao tentar salvar as alterações: {e}")

if __name__ == '__main__':
    cleanup_invalid_vinculos()