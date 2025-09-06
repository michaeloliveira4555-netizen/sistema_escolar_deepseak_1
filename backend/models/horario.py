from __future__ import annotations
import typing as t
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .disciplina import Disciplina
    from .instrutor import Instrutor
    from .semana import Semana # Importa o novo modelo

class Horario(db.Model):
    __tablename__ = 'horarios'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    pelotao: Mapped[str] = mapped_column(db.String(50), nullable=False)
    dia_semana: Mapped[str] = mapped_column(db.String(20), nullable=False)
    periodo: Mapped[int] = mapped_column(nullable=False)
    duracao: Mapped[int] = mapped_column(default=1)

    # --- ALTERAÇÃO AQUI ---
    # Adiciona a chave estrangeira para a semana
    semana_id: Mapped[int] = mapped_column(db.ForeignKey('semanas.id'), nullable=False)

    disciplina_id: Mapped[int] = mapped_column(db.ForeignKey('disciplinas.id'), nullable=False)
    instrutor_id: Mapped[int] = mapped_column(db.ForeignKey('instrutores.id'), nullable=False)

    status: Mapped[str] = mapped_column(db.String(20), default='pendente', nullable=False)

    # Relacionamentos
    semana: Mapped["Semana"] = relationship() # Adiciona o relacionamento
    disciplina: Mapped["Disciplina"] = relationship()
    instrutor: Mapped["Instrutor"] = relationship()

    def __init__(self, pelotao: str, dia_semana: str, periodo: int, semana_id: int, disciplina_id: int, instrutor_id: int, duracao: int = 1, status: str = 'pendente', **kw: t.Any) -> None:
        super().__init__(pelotao=pelotao, dia_semana=dia_semana, periodo=periodo, semana_id=semana_id, disciplina_id=disciplina_id, instrutor_id=instrutor_id, duracao=duracao, status=status, **kw)

    def __repr__(self):
        return f"<Horario id={self.id} pelotao='{self.pelotao}' semana_id={self.semana_id}>"