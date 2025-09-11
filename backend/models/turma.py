from __future__ import annotations
import typing as t
import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .aluno import Aluno

class Turma(db.Model):
    __tablename__ = 'turmas'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False) # Ex: "1º Pelotão", "Turma de Formação 2025"
    ano: Mapped[int] = mapped_column(nullable=True)

    # Uma turma pode ter vários alunos
    alunos: Mapped[list["Aluno"]] = relationship(back_populates="turma")

    def __init__(self, nome: str, ano: t.Optional[int] = None, **kw: t.Any) -> None:
        super().__init__(nome=nome, ano=ano, **kw)

    @db.validates('nome')
    def validate_nome(self, key, nome):
        if not nome:
            raise ValueError("Nome da turma não pode ser vazio.")
        return nome

    @db.validates('ano')
    def validate_ano(self, key, ano):
        if ano and (ano < 2000 or ano > datetime.date.today().year + 5):
            raise ValueError("Ano inválido.")
        return ano

    def __repr__(self):
        return f"<Turma id={self.id} nome='{self.nome}'>"