from __future__ import annotations
import typing as t
from datetime import datetime
from .database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship

if t.TYPE_CHECKING:
    from .user import User
    from .school import School

class UserSchool(db.Model):
    __tablename__ = 'user_schools'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    school_id: Mapped[int] = mapped_column(db.ForeignKey('schools.id'), nullable=False)
    role: Mapped[str] = mapped_column(db.String(20), nullable=False)  # 'aluno', 'instrutor', 'admin_escola'
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped['User'] = relationship('User', back_populates='user_schools')
    school: Mapped['School'] = relationship('School', back_populates='user_schools')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'school_id', name='uq_user_school'),
    )

    def __repr__(self) -> str:
        return f"<UserSchool user_id={self.user_id} school_id={self.school_id} role={self.role}>"
