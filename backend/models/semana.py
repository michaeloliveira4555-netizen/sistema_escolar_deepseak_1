from __future__ import annotations
import typing as t
from datetime import date
from .database import db
from sqlalchemy.orm import Mapped, mapped_column

class Semana(db.Model):
    __tablename__ = 'semanas'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(db.String(100), nullable=False) # Ex: "Semana 1", "Semana de Provas"
    data_inicio: Mapped[date] = mapped_column(db.Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(db.Date, nullable=False)

    def __init__(self, nome: str, data_inicio: date, data_fim: date, **kw: t.Any) -> None:
        super().__init__(nome=nome, data_inicio=data_inicio, data_fim=data_fim, **kw)

    def __repr__(self):
        return f"<Semana id={self.id} nome='{self.nome}'>"