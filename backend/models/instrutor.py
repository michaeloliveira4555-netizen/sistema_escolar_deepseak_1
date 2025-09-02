from .disciplina import Disciplina
from ..extensions import db
from .user import User

class Instrutor(db.Model):
    __tablename__ = 'instrutores'

    id = db.Column(db.Integer, primary_key=True)
    
    # Relação com o usuário principal
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    user = db.relationship('User', back_populates='instrutor_profile')

    # Campos específicos do instrutor
    nome_completo = db.Column(db.String(120), nullable=False)
    especializacao = db.Column(db.String(100), nullable=True) # Ex: 'Tiro', 'Defesa Pessoal'
    
    # Adicionando um campo para a matrícula do instrutor, que pode ser diferente do login
    matricula_instrutor = db.Column(db.String(20), unique=True, nullable=False)

    # ADICIONE A LINHA ABAIXO PARA CRIAR A RELAÇÃO DE VOLTA
    disciplinas = db.relationship('Disciplina', back_populates='instrutor')
    
    def __repr__(self):
        return f'<Instrutor {self.nome_completo}>'