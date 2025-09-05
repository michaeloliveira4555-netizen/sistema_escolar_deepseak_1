# backend/models/__init__.py
# Este arquivo torna a pasta 'models' um pacote Python
# e facilita a importação dos modelos.

from .user import User
from .aluno import Aluno
from .instrutor import Instrutor
from .disciplina import Disciplina
from .historico import HistoricoAluno
from .historico_disciplina import HistoricoDisciplina
from .image_asset import ImageAsset
from .site_config import SiteConfig