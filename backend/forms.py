from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    id_func = StringField('ID Funcional', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repita a Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Função', choices=[('aluno', 'Aluno'), ('instrutor', 'Instrutor')], validators=[DataRequired()])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    login_identifier = StringField('ID Funcional ou Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Login')

class AlunoProfileForm(FlaskForm):
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=20)])
    opm = StringField('OPM', validators=[DataRequired(), Length(max=50)])
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    num_aluno = StringField('Número do Aluno', validators=[Length(max=20)])
    funcao_atual = StringField('Função Atual', validators=[Length(max=50)])
    foto_perfil = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png'])])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class AdminCreateAlunoForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repita a Senha', validators=[DataRequired(), EqualTo('password')])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=20)])
    opm = StringField('OPM', validators=[DataRequired(), Length(max=50)])
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    funcao_atual = StringField('Função Atual', validators=[Length(max=50)])
    foto_perfil = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Cadastrar Aluno')

FUNCAO_CHOICES = [('', 'Selecione uma função')] + [
    ('P2', 'P2'), ('P3', 'P3'), ('P4', 'P4'), ('P5', 'P5'),
    ('Aux Disc', 'Aux Disc'), ('Aux Cia', 'Aux Cia'), ('Aux Pel', 'Aux Pel'),
    ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('C5', 'C5'),
    ('Formatura', 'Formatura'), ('Obras', 'Obras'), ('Atletismo', 'Atletismo'),
    ('Jubileu', 'Jubileu'), ('Dia da Criança', 'Dia da Criança'), ('Seminário', 'Seminário'),
    ('Chefe de Turma', 'Chefe de Turma'), ('Correio', 'Correio'),
    ('Cmt 1° GPM', 'Cmt 1° GPM'), ('Cmt 2° GPM', 'Cmt 2° GPM'), ('Cmt 3° GPM', 'Cmt 3° GPM'),
    ('Socorrista 1', 'Socorrista 1'), ('Socorrista 2', 'Socorrista 2'),
    ('Motorista 1', 'Motorista 1'), ('Motorista 2', 'Motorista 2'),
    ('Telefonista 1', 'Telefonista 1'), ('Telefonista 2', 'Telefonista 2')
]

class AdminEditAlunoForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=20)])
    opm = StringField('OPM', validators=[DataRequired(), Length(max=50)])
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    funcao_atual = SelectField('Função Atual', choices=FUNCAO_CHOICES, validators=[Length(max=50)])
    foto_perfil = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Salvar Alterações')

class SelfEditAlunoForm(FlaskForm):
    funcao_atual = SelectField('Função Atual', choices=FUNCAO_CHOICES, validators=[Length(max=50)])
    foto_perfil = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png'])])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class InstrutorForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=120)])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=14)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repita a Senha', validators=[DataRequired(), EqualTo('password')])
    especializacao = StringField('Especialização', validators=[DataRequired(), Length(max=100)])
    formacao = StringField('Formação', validators=[DataRequired(), Length(max=100)])
    telefone = StringField('Telefone', validators=[Length(max=15)])
    submit = SubmitField('Cadastrar Instrutor')

class EditInstrutorForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=120)])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=14)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    especializacao = StringField('Especialização', validators=[DataRequired(), Length(max=100)])
    formacao = StringField('Formação', validators=[DataRequired(), Length(max=100)])
    telefone = StringField('Telefone', validators=[Length(max=15)])
    submit = SubmitField('Salvar Alterações')

class DisciplinaForm(FlaskForm):
    materia = StringField('Matéria', validators=[DataRequired(), Length(max=100)])
    carga_horaria_prevista = IntegerField('Carga Horária Prevista', validators=[DataRequired()])
    submit = SubmitField('Adicionar Disciplina')

class EditDisciplinaForm(FlaskForm):
    carga_horaria = IntegerField('Carga Horária', validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class TurmaForm(FlaskForm):
    nome = StringField('Nome da Turma', validators=[DataRequired(), Length(max=100)])
    ano = IntegerField('Ano', validators=[DataRequired()])
    alunos_ids = SelectMultipleField('Alunos', coerce=int)
    submit = SubmitField('Cadastrar Turma')

class CargosTurmaForm(FlaskForm):
    # This form will be dynamically generated in the controller
    submit = SubmitField('Salvar Cargos')

class PreRegistrationForm(FlaskForm):
    id_func = StringField('ID Funcional', validators=[DataRequired(), Length(min=4, max=20)])
    role = SelectField('Função', choices=[('aluno', 'Aluno'), ('instrutor', 'Instrutor')], validators=[DataRequired()])
    submit = SubmitField('Pré-cadastrar')
