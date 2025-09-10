#!/usr/bin/env python3
"""
Script para debugar as associações disciplina-instrutor-turma
Execute: python debug_associacoes.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models.database import db
from backend.models.disciplina_turma import DisciplinaTurma
from backend.models.disciplina import Disciplina
from backend.models.instrutor import Instrutor
from backend.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import joinedload

def debug_associacoes():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG: ASSOCIAÇÕES DISCIPLINA-TURMA-INSTRUTOR ===\n")
        
        # 1. Primeiro, verificar se existe a disciplina específica
        disciplina_procurada = "Sistemas de Correição: Atribuição do Escrivão PJM"
        disciplina = db.session.execute(
            select(Disciplina).where(Disciplina.materia == disciplina_procurada)
        ).scalar_one_or_none()
        
        if disciplina:
            print(f"✅ Disciplina encontrada: {disciplina.materia} (ID: {disciplina.id})")
        else:
            print(f"❌ Disciplina '{disciplina_procurada}' NÃO encontrada!")
            print("Disciplinas disponíveis:")
            todas_disciplinas = db.session.scalars(select(Disciplina)).all()
            for d in todas_disciplinas:
                print(f"  - {d.materia}")
            return
        
        # 2. Verificar se existe o instrutor Romario Pintasilgo
        instrutor = db.session.execute(
            select(Instrutor)
            .options(joinedload(Instrutor.user))
            .join(User)
            .where(User.nome_completo.ilike('%Romario%Pintasilgo%'))
        ).scalar_one_or_none()
        
        if instrutor:
            print(f"✅ Instrutor encontrado: {instrutor.user.nome_completo} (ID: {instrutor.id})")
        else:
            print("❌ Instrutor 'Romario Pintasilgo' NÃO encontrado!")
            print("Instrutores disponíveis:")
            todos_instrutores = db.session.scalars(
                select(Instrutor).options(joinedload(Instrutor.user))
            ).all()
            for inst in todos_instrutores:
                nome = inst.user.nome_completo if inst.user else "Sem nome"
                print(f"  - {nome} (ID: {inst.id})")
            return
        
        # 3. Verificar associação para Turma 5
        pelotao = "5° Pelotão"
        associacao = db.session.execute(
            select(DisciplinaTurma).where(
                DisciplinaTurma.disciplina_id == disciplina.id,
                DisciplinaTurma.pelotao == pelotao
            )
        ).scalar_one_or_none()
        
        if associacao:
            print(f"✅ Associação encontrada para {pelotao}:")
            print(f"   - Disciplina: {disciplina.materia}")
            print(f"   - Instrutor 1: {associacao.instrutor_id_1}")
            print(f"   - Instrutor 2: {associacao.instrutor_id_2}")
            
            # Verificar se o Romario está vinculado
            if associacao.instrutor_id_1 == instrutor.id or associacao.instrutor_id_2 == instrutor.id:
                print(f"✅ ROMARIO ESTÁ VINCULADO à disciplina no {pelotao}!")
            else:
                print(f"❌ ROMARIO NÃO ESTÁ VINCULADO à disciplina no {pelotao}")
                print(f"   Para vincular, execute o seguinte SQL:")
                print(f"   UPDATE disciplina_turmas SET instrutor_id_1 = {instrutor.id} WHERE id = {associacao.id};")
        else:
            print(f"❌ NÃO existe associação da disciplina '{disciplina.materia}' com '{pelotao}'")
            print(f"   Para criar, execute:")
            print(f"   INSERT INTO disciplina_turmas (disciplina_id, pelotao, instrutor_id_1) VALUES ({disciplina.id}, '{pelotao}', {instrutor.id});")
        
        # 4. Testar a query que o sistema usa
        print(f"\n=== TESTANDO A QUERY DO SISTEMA ===")
        query_sistema = (
            select(DisciplinaTurma)
            .options(joinedload(DisciplinaTurma.disciplina))
            .where(
                DisciplinaTurma.pelotao == pelotao,
                (DisciplinaTurma.instrutor_id_1 == instrutor.id) | (DisciplinaTurma.instrutor_id_2 == instrutor.id)
            )
            .order_by(DisciplinaTurma.disciplina_id)
        )
        
        resultados = db.session.scalars(query_sistema).unique().all()
        
        print(f"Query retornou {len(resultados)} disciplina(s) para o instrutor {instrutor.user.nome_completo} no {pelotao}:")
        for res in resultados:
            print(f"  - {res.disciplina.materia}")
        
        if len(resultados) == 0:
            print("❌ A query do sistema NÃO retorna nenhuma disciplina!")
            print("   Isso explica por que a disciplina não aparece no dropdown.")

if __name__ == '__main__':
    debug_associacoes()