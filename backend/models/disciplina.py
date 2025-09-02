from __future__ import annotations
import typing as t
from datetime import datetime
from ..extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .instrutor import Instrutor
    from .historico_disciplina import HistoricoDisciplina


class Disciplina(db.Model):
    __tablename__ = 'disciplinas'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    materia: Mapped[str] = mapped_column(db.String(100), unique=True)
    carga_horaria_prevista: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    instrutor_id: Mapped[t.Optional[int]] = mapped_column(db.ForeignKey('instrutores.id'))
    instrutor: Mapped[t.Optional["Instrutor"]] = relationship(back_populates="disciplinas")
    
    historico_disciplinas: Mapped[list["HistoricoDisciplina"]] = relationship(back_populates="disciplina")
    
    def __init__(self, materia: str, carga_horaria_prevista: int, 
                 instrutor_id: t.Optional[int] = None, **kw: t.Any) -> None:
        super().__init__(materia=materia, carga_horaria_prevista=carga_horaria_prevista, 
                         instrutor_id=instrutor_id, **kw)

    def __repr__(self):
        return f"<Disciplina id={self.id} materia='{self.materia}'>"