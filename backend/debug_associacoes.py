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
        
        # Buscar todas as associações
        query = (
            select(DisciplinaTurma)
            .options(
                joinedload(DisciplinaTurma.disciplina),
                joinedload(DisciplinaTurma.instrutor_1).joinedload(Instrutor.user),
                joinedload(DisciplinaTurma.instrutor_2).joinedload(Instrutor.user)
            )
            .order_by(DisciplinaTurma.pelotao, DisciplinaTurma.disciplina_id)
        )
        
        associacoes = db.session.scalars(query).unique().all()
        
        print(f"Total de associações encontradas: {len(associacoes)}")
        print("-" * 80)
        
        pelotoes = {}
        
        for assoc in associacoes:
            pelotao = assoc.pelotao
            if pelotao not in pelotoes:
                pelotoes[pelotao] = []
            
            instrutor1_info = "NENHUM"
            if assoc.instrutor_1:
                nome1 = "SEM USER"
                if assoc.instrutor_1.user:
                    nome1 = assoc.instrutor_1.user.nome_completo or assoc.instrutor_1.user.username
                instrutor1_info = f"ID:{assoc.instrutor_id_1} - {nome1}"
            
            instrutor2_info = "NENHUM"
            if assoc.instrutor_2:
                nome2 = "SEM USER"
                if assoc.instrutor_2.user:
                    nome2 = assoc.instrutor_2.user.nome_completo or assoc.instrutor_2.user.username
                instrutor2_info = f"ID:{assoc.instrutor_id_2} - {nome2}"
            
            pelotoes[pelotao].append({
                'disciplina': assoc.disciplina.materia,
                'disciplina_id': assoc.disciplina.id,
                'instrutor1': instrutor1_info,
                'instrutor2': instrutor2_info
            })
        
        # Exibir por pelotão
        for pelotao, disciplinas in pelotoes.items():
            print(f"\n🏫 {pelotao}:")
            print("   " + "="*60)
            
            for disc in disciplinas:
                print(f"   📚 {disc['disciplina']} (ID: {disc['disciplina_id']})")
                print(f"      👨‍🏫 Instrutor 1: {disc['instrutor1']}")
                print(f"      👨‍🏫 Instrutor 2: {disc['instrutor2']}")
                print()
        
        # Verificar instrutores sem associação
        print("\n" + "="*80)
        print("🔍 VERIFICAÇÃO DE INSTRUTORES SEM ASSOCIAÇÃO")
        print("="*80)
        
        todos_instrutores = db.session.scalars(
            select(Instrutor).options(joinedload(Instrutor.user)).order_by(Instrutor.id)
        ).all()
        
        instrutores_associados = set()
        for assoc in associacoes:
            if assoc.instrutor_id_1:
                instrutores_associados.add(assoc.instrutor_id_1)
            if assoc.instrutor_id_2:
                instrutores_associados.add(assoc.instrutor_id_2)
        
        print(f"Total de instrutores: {len(todos_instrutores)}")
        print(f"Instrutores com associação: {len(instrutores_associados)}")
        
        instrutores_sem_associacao = []
        for inst in todos_instrutores:
            if inst.id not in instrutores_associados:
                nome = "SEM USER"
                if inst.user:
                    nome = inst.user.nome_completo or inst.user.username
                instrutores_sem_associacao.append(f"ID:{inst.id} - {nome}")
        
        if instrutores_sem_associacao:
            print("\n❌ Instrutores SEM associação:")
            for inst in instrutores_sem_associacao:
                print(f"   {inst}")
        else:
            print("\n✅ Todos os instrutores têm associação!")
        
        print("\n" + "="*80)
        print("💡 DICAS PARA CORREÇÃO:")
        print("="*80)
        print("1. Se um instrutor não aparece na lista, vá em 'Disciplinas' → 'Gerenciar'")
        print("2. Edite a disciplina e atribua o instrutor ao