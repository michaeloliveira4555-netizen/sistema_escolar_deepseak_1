from __future__ import annotations
import typing as t
from datetime import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .user import User

class Instrutor(db.Model):
    __tablename__ = 'instrutores'

    id: Mapped[int] = mapped_column(primary_key=True)
    matricula: Mapped[str] = mapped_column(db.String(14), unique=True)
    especializacao: Mapped[str] = mapped_column(db.String(100), nullable=False)
    formacao: Mapped[str] = mapped_column(db.String(100))
    telefone: Mapped[t.Optional[str]] = mapped_column(db.String(15))
    credor: Mapped[t.Optional[str]] = mapped_column(db.String(100)) # <-- NOVO CAMPO ADICIONADO
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), unique=True)
    user: Mapped["User"] = relationship(back_populates="instrutor_profile")

    def __init__(self, user_id: int, matricula: str, especializacao: str, formacao: str,
                 telefone: t.Optional[str] = None, credor: t.Optional[str] = None, **kw: t.Any) -> None:
        super().__init__(user_id=user_id, matricula=matricula, especializacao=especializacao, formacao=formacao,
                         telefone=telefone, credor=credor, **kw)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nome': self.user.username if self.user else None,
            'matricula': self.matricula,
            'especialidade': self.especializacao,
            'formacao': self.formacao,
            'telefone': self.telefone,
            'credor': self.credor
        }

    def __repr__(self):
        return f"<Instrutor id={self.id} matricula='{self.matricula}'>"