import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
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

def optimize_image(file_path, max_width=800, max_height=600, quality=85):
    """Otimiza a imagem redimensionando e comprimindo"""
    try:
        with Image.open(file_path) as img:
            # Converte para RGB se necessário
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensiona mantendo proporção
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Salva com qualidade otimizada
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"Erro ao otimizar imagem: {e}")
        return False

def get_file_hash(file_path):
    """Gera hash MD5 do arquivo para verificar duplicatas"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()