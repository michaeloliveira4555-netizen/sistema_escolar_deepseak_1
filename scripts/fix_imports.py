#!/usr/bin/env python3
"""
Script para corrigir automaticamente imports relativos
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitui imports relativos por absolutos
    content = re.sub(r'from \.\.(\w+) import', r'from \1 import', content)
    content = re.sub(r'from \.\.\.(\w+) import', r'from \1 import', content)
    content = re.sub(r'import \.\.(\w+)', r'import \1', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Corrigido: {file_path}")

def main():
    # Percorre todos os arquivos .py no projeto
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                fix_imports_in_file(file_path)

if __name__ == '__main__':
    print("Corrigindo imports relativos...")
    main()
    print("Correção concluída!")