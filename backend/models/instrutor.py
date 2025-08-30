from __future__ import annotations
import typing as t
from datetime import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .user import User
    from .disciplina import Disciplina


class Instrutor(db.Model):
    __tablename__ = 'instrutores'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # ALTERADO: O campo 'cpf' foi substituído por 'matricula'
    matricula: Mapped[str] = mapped_column(db.String(14), unique=True)
    especializacao: Mapped[str] = mapped_column(db.String(100), nullable=False)
    formacao: Mapped[str] = mapped_column(db.String(100))
    telefone: Mapped[t.Optional[str]] = mapped_column(db.String(15))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), unique=True)
    user: Mapped["User"] = relationship(back_populates="instrutor_profile")

    disciplinas: Mapped[list["Disciplina"]] = relationship(back_populates="instrutor")
    
    # ALTERADO: O construtor foi atualizado para usar 'matricula'
    def __init__(self, user_id: int, matricula: str, especializacao: str, formacao: str, 
                 telefone: t.Optional[str] = None, **kw: t.Any) -> None:
        super().__init__(user_id=user_id, matricula=matricula, especializacao=especializacao, formacao=formacao, 
                         telefone=telefone, **kw)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nome': self.user.username if self.user else None,
            # ALTERADO: O campo 'cpf' foi substituído por 'matricula'
            'matricula': self.matricula,
            'especialidade': self.especializacao,
            'formacao': self.formacao,
            'telefone': self.telefone
        }

    def __repr__(self):
        # ALTERADO: O campo 'cpf' foi substituído por 'matricula'
        return f"<Instrutor id={self.id} matricula='{self.matricula}'>"
