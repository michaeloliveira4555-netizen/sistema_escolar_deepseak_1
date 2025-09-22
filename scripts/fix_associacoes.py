#!/usr/bin/env python3
"""
Script para corrigir associações disciplina-instrutor-turma
Execute: python fix_associacoes.py
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
from backend.models.turma import Turma
from sqlalchemy import select
from sqlalchemy.orm import joinedload

def fix_associacoes():
    app = create_app()
    
    with app.app_context():
        print("=== SCRIPT DE CORREÇÃO DE ASSOCIAÇÕES ===\n")
        
        # 1. Verificar se existem turmas sem associações de disciplinas
        print("1. Verificando turmas sem associações...")
        
        turmas = db.session.scalars(select(Turma)).all()
        disciplinas = db.session.scalars(select(Disciplina)).all()
        
        for turma in turmas:
            print(f"\nVerificando turma: {turma.nome}")
            
            for disciplina in disciplinas:
                # Verificar se existe associação
                associacao_existente = db.session.execute(
                    select(DisciplinaTurma).where(
                        DisciplinaTurma.disciplina_id == disciplina.id,
                        DisciplinaTurma.pelotao == turma.nome
                    )
                ).scalar_one_or_none()
                
                if not associacao_existente:
                    print(f"  ❌ Faltando associação: {disciplina.materia}")
                    
                    # Criar associação sem instrutor
                    nova_associacao = DisciplinaTurma(
                        disciplina_id=disciplina.id,
                        pelotao=turma.nome,
                        instrutor_id_1=None,
                        instrutor_id_2=None
                    )
                    db.session.add(nova_associacao)
                    print(f"  ✅ Criada associação para {disciplina.materia}")
                else:
                    print(f"  ✅ Associação existe: {disciplina.materia}")
        
        # Commit das novas associações
        try:
            db.session.commit()
            print("\n✅ Associações criadas com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao criar associações: {e}")
            return
        
        # 2. Buscar caso específico: Romario Pintasilgo + Sistemas de Correição
        print("\n2. Verificando caso específico...")
        
        # Buscar disciplina específica
        disciplina_nome = "Sistemas de Correição: Atribuição do Escrivão PJM"
        disciplina = db.session.execute(
            select(Disciplina).where(Disciplina.materia == disciplina_nome)
        ).scalar_one_or_none()
        
        if not disciplina:
            print(f"❌ Disciplina '{disciplina_nome}' não encontrada!")
            print("Disciplinas disponíveis:")
            for d in disciplinas:
                if "Sistemas" in d.materia or "Correição" in d.materia:
                    print(f"  - {d.materia}")
            return
        
        print(f"✅ Disciplina encontrada: {disciplina.materia} (ID: {disciplina.id})")
        
        # Buscar instrutor Romario
        instrutor = db.session.execute(
            select(Instrutor)
            .options(joinedload(Instrutor.user))
            .join(User)
            .where(User.nome_completo.ilike('%Romario%'))
        ).scalar_one_or_none()
        
        if not instrutor:
            print("❌ Instrutor 'Romario' não encontrado!")
            print("Instrutores disponíveis:")
            todos_instrutores = db.session.scalars(
                select(Instrutor).options(joinedload(Instrutor.user))
            ).all()
            for inst in todos_instrutores:
                nome = inst.user.nome_completo if inst.user else "Sem nome"
                print(f"  - {nome} (ID: {inst.id})")
            return
        
        print(f"✅ Instrutor encontrado: {instrutor.user.nome_completo} (ID: {instrutor.id})")
        
        # 3. Verificar e corrigir associação para Turma 5
        pelotao = "5° Pelotão"
        
        associacao = db.session.execute(
            select(DisciplinaTurma).where(
                DisciplinaTurma.disciplina_id == disciplina.id,
                DisciplinaTurma.pelotao == pelotao
            )
        ).scalar_one_or_none()
        
        if associacao:
            print(f"✅ Associação encontrada para {pelotao}")
            print(f"   Instrutor 1: {associacao.instrutor_id_1}")
            print(f"   Instrutor 2: {associacao.instrutor_id_2}")
            
            # Verificar se Romario já está vinculado
            if associacao.instrutor_id_1 == instrutor.id or associacao.instrutor_id_2 == instrutor.id:
                print(f"✅ Romario JÁ está vinculado!")
            else:
                print(f"❌ Romario NÃO está vinculado. Corrigindo...")
                
                # Vincular Romario como instrutor 1 (se vazio) ou instrutor 2
                if associacao.instrutor_id_1 is None:
                    associacao.instrutor_id_1 = instrutor.id
                    print(f"✅ Romario vinculado como Instrutor 1")
                elif associacao.instrutor_id_2 is None:
                    associacao.instrutor_id_2 = instrutor.id
                    print(f"✅ Romario vinculado como Instrutor 2")
                else:
                    print(f"⚠️  Ambos slots de instrutor estão ocupados!")
                    print(f"   Substituindo Instrutor 1...")
                    associacao.instrutor_id_1 = instrutor.id
                
                try:
                    db.session.commit()
                    print(f"✅ Associação atualizada com sucesso!")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Erro ao atualizar associação: {e}")
        else:
            print(f"❌ Associação não encontrada para {pelotao}")
        
        # 4. Testar a query final
        print(f"\n3. Testando query final...")
        
        query_final = (
            select(DisciplinaTurma)
            .options(joinedload(DisciplinaTurma.disciplina))
            .where(
                DisciplinaTurma.pelotao == pelotao,
                (DisciplinaTurma.instrutor_id_1 == instrutor.id) | (DisciplinaTurma.instrutor_id_2 == instrutor.id)
            )
        )
        
        resultados = db.session.scalars(query_final).unique().all()
        
        print(f"Query retorna {len(resultados)} disciplina(s):")
        for resultado in resultados:
            print(f"  - {resultado.disciplina.materia}")
        
        if len(resultados) == 0:
            print("❌ AINDA há problema! Verificando todas as associações do instrutor...")
            
            todas_associacoes_instrutor = db.session.scalars(
                select(DisciplinaTurma)
                .options(joinedload(DisciplinaTurma.disciplina))
                .where(
                    (DisciplinaTurma.instrutor_id_1 == instrutor.id) | (DisciplinaTurma.instrutor_id_2 == instrutor.id)
                )
            ).all()
            
            print(f"Instrutor tem {len(todas_associacoes_instrutor)} associação(ões) total:")
            for assoc in todas_associacoes_instrutor:
                print(f"  - {assoc.disciplina.materia} no {assoc.pelotao}")
        else:
            print("✅ Query funciona corretamente!")

if __name__ == '__main__':
    fix_associacoes()