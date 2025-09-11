from __future__ import annotations
import typing as t
from datetime import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .historico_disciplina import HistoricoDisciplina


class Disciplina(db.Model):
    __tablename__ = 'disciplinas'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    materia: Mapped[str] = mapped_column(db.String(100), unique=True)
    carga_horaria_prevista: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    historico_disciplinas: Mapped[list["HistoricoDisciplina"]] = relationship(back_populates="disciplina")
    
    def __init__(self, materia: str, carga_horaria_prevista: int, **kw: t.Any) -> None:
        super().__init__(materia=materia, carga_horaria_prevista=carga_horaria_prevista, **kw)

    @db.validates('materia')
    def validate_materia(self, key, materia):
        if not materia:
            raise ValueError("Matéria não pode ser vazia.")
        return materia

    @db.validates('carga_horaria_prevista')
    def validate_carga_horaria_prevista(self, key, carga_horaria_prevista):
        if carga_horaria_prevista < 0:
            raise ValueError("Carga horária não pode ser negativa.")
        return carga_horaria_prevista

    def __repr__(self):
        return f"<Disciplina id={self.id} materia='{self.materia}'>"