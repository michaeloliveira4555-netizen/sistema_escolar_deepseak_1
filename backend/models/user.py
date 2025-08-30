from __future__ import annotations
import typing as t
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .aluno import Aluno
    from .instrutor import Instrutor


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(80), unique=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(256))
    role: Mapped[str] = mapped_column(db.String(20), default='aluno')

    aluno_profile: Mapped[t.Optional["Aluno"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    instrutor_profile: Mapped[t.Optional["Instrutor"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __init__(self, username: str, email: str, role: str, **kw: t.Any) -> None:
        super().__init__(**kw)
        self.username = username
        self.email = email
        self.role = role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"