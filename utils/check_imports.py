#!/usr/bin/env python3
"""
Script para verificar se todos os imports estão corretos
"""
import sys
from pathlib import Path

# Adiciona o diretório atual ao path do Python
sys.path.append(str(Path(__file__).parent))

print("=== VERIFICAÇÃO DE IMPORTS ===")

try:
    from models.user import User
    print("✓ models.user importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar models.user: {e}")

try:
    from models.aluno import Aluno
    print("✓ models.aluno importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar models.aluno: {e}")

try:
    from models.instrutor import Instrutor
    print("✓ models.instrutor importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar models.instrutor: {e}")

try:
    from models.database import db
    print("✓ models.database importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar models.database: {e}")

try:
    from utils.security import hash_password
    print("✓ utils.security importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar utils.security: {e}")

try:
    from utils.validators import validate_email
    print("✓ utils.validators importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar utils.validators: {e}")

try:
    from services.auth_service import AuthService
    print("✓ services.auth_service importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar services.auth_service: {e}")

try:
    from services.aluno_service import AlunoService
    print("✓ services.aluno_service importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar services.aluno_service: {e}")

try:
    from controllers.auth_controller import auth_bp
    print("✓ controllers.auth_controller importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar controllers.auth_controller: {e}")

try:
    from controllers.aluno_controller import aluno_bp
    print("✓ controllers.aluno_controller importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar controllers.aluno_controller: {e}")

print("\n=== VERIFICAÇÃO CONCLUÍDA ===")