from __future__ import annotations
import typing as t
from datetime import date
from ..extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .user import User
    from .historico import HistoricoAluno
    from .historico_disciplina import HistoricoDisciplina


class Aluno(db.Model):
    __tablename__ = 'alunos'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # --- CAMPO FALTANTE ADICIONADO AQUI ---
    nome_completo: Mapped[str] = mapped_column(db.String(120))
    
    # O resto dos seus campos, mantidos como estão
    id_aluno: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=True)
    matricula: Mapped[str] = mapped_column(db.String(20), unique=True)
    opm: Mapped[str] = mapped_column(db.String(50))
    num_aluno: Mapped[str] = mapped_column(db.String(20), nullable=True)
    pelotao: Mapped[str] = mapped_column(db.String(20))
    funcao_atual: Mapped[t.Optional[str]] = mapped_column(db.String(50))
    foto_perfil: Mapped[str] = mapped_column(db.String(255), default='default.png')
    telefone: Mapped[t.Optional[str]] = mapped_column(db.String(20))
    data_nascimento: Mapped[t.Optional[date]] = mapped_column(db.Date)
    
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), unique=True)
    user: Mapped["User"] = relationship(back_populates="aluno_profile")

    historico: Mapped[list["HistoricoAluno"]] = relationship(back_populates="aluno")
    historico_disciplinas: Mapped[list["HistoricoDisciplina"]] = relationship(back_populates="aluno")

    # Removendo o __init__ para usar o padrão do SQLAlchemy que funciona melhor com Mapped
    
    def __repr__(self):
        # Corrigindo a referência para self.matricula
        return f"<Aluno id={self.id} matricula='{self.matricula}'>"