from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    id_func = db.Column(db.String(20), unique=True, nullable=False)

    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)

    nome_completo = db.Column(db.String(120), nullable=True)
    nome_de_guerra = db.Column(db.String(50), nullable=True)

    role = db.Column(db.String(20), nullable=False, default='aluno')
    is_active = db.Column(db.Boolean, default=False, nullable=False)

    aluno_profile = db.relationship('Aluno', back_populates='user', uselist=False, cascade="all, delete-orphan")
    instrutor_profile = db.relationship('Instrutor', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username or self.id_func}>'