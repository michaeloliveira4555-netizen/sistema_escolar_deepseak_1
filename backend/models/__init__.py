# backend/models/__init__.py

# Importe todas as suas classes de modelo aqui.
# Isso garante que o SQLAlchemy conheça todas elas
# antes de tentar construir as relações.

from .user import User
from .aluno import Aluno
from .instrutor import Instrutor
from .disciplina import Disciplina
from .historico import HistoricoAluno
from .historico_disciplina import HistoricoDisciplina
# Adicione aqui qualquer outro modelo que você criar.