from __future__ import annotations
import typing as t
from datetime import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .historico_disciplina import HistoricoDisciplina
    from .disciplina_turma import DisciplinaTurma
    from .school import School


class Disciplina(db.Model):
    __tablename__ = 'disciplinas'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    materia: Mapped[str] = mapped_column(db.String(100), unique=True)
    carga_horaria_prevista: Mapped[int] = mapped_column()
    ciclo: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1, server_default='1')
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    school_id: Mapped[int] = mapped_column(db.ForeignKey('schools.id'), nullable=False)
    school: Mapped["School"] = relationship(back_populates="disciplinas")
    
    historico_disciplinas: Mapped[list["HistoricoDisciplina"]] = relationship(back_populates="disciplina")
    associacoes_turmas: Mapped[list["DisciplinaTurma"]] = relationship(back_populates="disciplina_associada")
    
    def __init__(self, materia: str, carga_horaria_prevista: int, school_id: int, ciclo: int = 1, **kw: t.Any) -> None:
        super().__init__(materia=materia, carga_horaria_prevista=carga_horaria_prevista, school_id=school_id, ciclo=ciclo, **kw)

    def __repr__(self):
        return f"<Disciplina id={self.id} materia='{self.materia}' ciclo={self.ciclo}>"