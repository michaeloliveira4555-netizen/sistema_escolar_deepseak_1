import os
import uuid
from werkzeug.utils import secure_filename
import hashlib

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Gera um nome único para o arquivo"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}"

def optimize_image(file_path, max_width=1920, max_height=1080, quality=90):
    """
    Otimiza a imagem redimensionando e comprimindo.
    - LARGURA MÁXIMA AUMENTADA PARA 1920px PARA BANNERS DE ALTA QUALIDADE.
    - QUALIDADE AUMENTADA PARA 90.
    """
    try:
        # Importação condicional para evitar erro se PIL não estiver instalado
        from PIL import Image
        
        # Ignora a otimização para arquivos SVG
        if file_path.lower().endswith('.svg'):
            return True

        with Image.open(file_path) as img:
            # Converte para RGB se necessário (para salvar como JPEG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensiona mantendo a proporção apenas se a imagem for maior que os limites
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Salva com qualidade otimizada
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except ImportError:
        # Se a biblioteca PIL/Pillow não estiver instalada, apenas retorna True sem falhar
        print("AVISO: A biblioteca 'Pillow' não está instalada. Pulando otimização de imagem.")
        return True
    except Exception as e:
        print(f"Erro ao otimizar imagem {file_path}: {e}")
        return False

def get_file_hash(file_path):
    """Gera hash MD5 do arquivo para verificar duplicatas"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()