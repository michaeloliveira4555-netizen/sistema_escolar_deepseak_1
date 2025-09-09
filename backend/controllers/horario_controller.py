from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import select
from datetime import date # Importa 'date' para pegar a data atual

from ..models.database import db
from ..models.horario import Horario
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.semana import Semana
from utils.decorators import admin_or_programmer_required

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

# ETAPA 1: Seleção de Semana
@horario_bp.route('/')
@login_required
@admin_or_programmer_required
def index():
    semanas_raw = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()
    
    # --- LÓGICA DE STATUS ADICIONADA AQUI ---
    today = date.today()
    semanas_com_status = []
    for semana in semanas_raw:
        status = ''
        if semana.data_fim < today:
            status = 'passada'
        elif semana.data_inicio > today:
            status = 'futura'
        else: # Se a data de hoje está entre o início e o fim
            status = 'atual'
        semanas_com_status.append({'semana': semana, 'status': status})

    return render_template(
        'selecionar_semana.html', 
        title="Visualizar Quadro Horário",
        target_endpoint='horario.selecionar_turma_visualizacao',
        semanas=semanas_com_status
    )

@horario_bp.route('/selecionar-turma-edicao')
@login_required
@admin_or_programmer_required
def selecionar_turma_edicao():
    semanas_raw = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()

    # --- LÓGICA DE STATUS ADICIONADA AQUI ---
    today = date.today()
    semanas_com_status = []
    for semana in semanas_raw:
        status = ''
        if semana.data_fim < today:
            status = 'passada'
        elif semana.data_inicio > today:
            status = 'futura'
        else:
            status = 'atual'
        semanas_com_status.append({'semana': semana, 'status': status})

    return render_template(
        'selecionar_semana.html', 
        title="Editar Quadro Horário",
        target_endpoint='horario.selecionar_turma_para_editar',
        semanas=semanas_com_status
    )

# O restante do arquivo continua o mesmo...
@horario_bp.route('/visualizar/turma', methods=['POST'])
@login_required
@admin_or_programmer_required
def selecionar_turma_visualizacao():
    semana_id = request.form.get('semana_id')
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana inválida.", "danger")
        return redirect(url_for('horario.index'))
    return render_template(
        'selecionar_turma.html',
        title="Visualizar Quadro Horário",
        target_endpoint='horario.visualizar_quadro_horario',
        semana=semana
    )

@horario_bp.route('/editar/turma', methods=['POST'])
@login_required
@admin_or_programmer_required
def selecionar_turma_para_editar():
    semana_id = request.form.get('semana_id')
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana inválida.", "danger")
        return redirect(url_for('horario.selecionar_turma_edicao'))
    return render_template(
        'selecionar_turma.html',
        title="Editar Quadro Horário",
        target_endpoint='horario.editar_quadro_horario',
        semana=semana
    )

def construir_matriz_horario(pelotao, semana_id):
    a_disposicao = {'materia': 'A disposição do C Al /S Ens', 'instrutor': None, 'duracao': 1, 'is_disposicao': True}
    horario_matrix = [[a_disposicao for _ in range(7)] for _ in range(15)]
    dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']

    aulas_agendadas = db.session.scalars(
        select(Horario).where(Horario.pelotao == pelotao, Horario.semana_id == semana_id)
    ).all()

    for aula in aulas_agendadas:
        try:
            dia_idx = dias.index(aula.dia_semana)
            periodo_idx = aula.periodo - 1
            if 0 <= periodo_idx < 15 and 0 <= dia_idx < 7:
                instrutor_nome = "N/D"
                if aula.instrutor and aula.instrutor.user:
                    instrutor_nome = aula.instrutor.user.nome_completo or aula.instrutor.user.username
                
                aula_info = {
                    'materia': aula.disciplina.materia,
                    'instrutor': instrutor_nome, 'duracao': aula.duracao,
                    'status': aula.status, 'is_disposicao': False
                }
                horario_matrix[periodo_idx][dia_idx] = aula_info
                for i in range(1, aula.duracao):
                    if periodo_idx + i < 15:
                        horario_matrix[periodo_idx + i][dia_idx] = 'SKIP'
        except (ValueError, IndexError):
            continue
    return horario_matrix

@horario_bp.route('/visualizar', methods=['POST'])
@login_required
@admin_or_programmer_required
def visualizar_quadro_horario():
    pelotao = request.form.get('pelotao')
    semana_id = request.form.get('semana_id')
    semana = db.session.get(Semana, semana_id)

    if not all([pelotao, semana]):
        flash("Seleção inválida.", "warning")
        return redirect(url_for('horario.index'))
    
    horario_matrix = construir_matriz_horario(pelotao, semana_id)
    return render_template('quadro_horario.html', horario_matrix=horario_matrix, pelotao_selecionado=pelotao, semana_selecionada=semana)

@horario_bp.route('/editar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def editar_quadro_horario():
    if request.method == 'POST':
        pelotao = request.form.get('pelotao')
        semana_id = request.form.get('semana_id')
    else:
        pelotao = request.args.get('pelotao')
        semana_id = request.args.get('semana_id')

    semana = db.session.get(Semana, semana_id)
    if not all([pelotao, semana]):
        flash("Seleção inválida.", "warning")
        return redirect(url_for('horario.selecionar_turma_edicao'))
    
    horario_matrix = construir_matriz_horario(pelotao, semana_id)
    
    associacoes = db.session.scalars(select(DisciplinaTurma).filter_by(pelotao=pelotao)).all()
    disciplinas_disponiveis = [{"id": a.disciplina.id, "nome": a.disciplina.materia} for a in associacoes]
    instrutores_disponiveis, instrutores_ids = [], set()
    for a in associacoes:
        if a.instrutor_id_1 not in instrutores_ids:
            instrutores_disponiveis.append({"id": a.instrutor_1.id, "nome": a.instrutor_1.user.nome_completo or a.instrutor_1.user.username})
            instrutores_ids.add(a.instrutor_id_1)
        if a.instrutor_id_2 and a.instrutor_id_2 not in instrutores_ids:
            instrutores_disponiveis.append({"id": a.instrutor_2.id, "nome": a.instrutor_2.user.nome_completo or a.instrutor_2.user.username})
            instrutores_ids.add(a.instrutor_id_2)

    return render_template(
        'editar_quadro_horario.html', 
        horario_matrix=horario_matrix, 
        pelotao_selecionado=pelotao,
        semana_selecionada=semana,
        disciplinas_disponiveis=disciplinas_disponiveis,
        instrutores_disponiveis=instrutores_disponiveis
    )

@horario_bp.route('/salvar', methods=['POST'])
@login_required
@admin_or_programmer_required
def salvar_horario():
    data = request.json
    pelotao = data.get('pelotao')
    semana_id = data.get('semana_id')
    aulas_para_salvar = data.get('aulas', [])
    
    try:
        db.session.query(Horario).filter_by(pelotao=pelotao, semana_id=semana_id).delete()
        for aula_data in aulas_para_salvar:
            nova_aula = Horario(
                pelotao=pelotao,
                semana_id=int(semana_id),
                dia_semana=aula_data['dia'],
                periodo=int(aula_data['periodo']),
                disciplina_id=int(aula_data['disciplina_id']),
                instrutor_id=int(aula_data['instrutor_id']),
                duracao=int(aula_data['duracao']),
                status='confirmado' if current_user.role in ['admin', 'programador'] else 'pendente'
            )
            db.session.add(nova_aula)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Quadro horário salvo com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar horário: {e}")
        return jsonify({'success': False, 'message': 'Ocorreu um erro ao salvar o horário.'}), 500

@horario_bp.route('/aprovar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def aprovar_horarios():
    if request.method == 'POST':
        horario_id = request.form.get('horario_id')
        action = request.form.get('action')
        
        horario = db.session.get(Horario, horario_id)
        
        if horario:
            if action == 'aprovar':
                horario.status = 'confirmado'
                flash(f'Aula de {horario.disciplina.materia} aprovada com sucesso!', 'success')
            elif action == 'negar':
                db.session.delete(horario)
                flash(f'Aula de {horario.disciplina.materia} negada e removida com sucesso!', 'warning')
            
            db.session.commit()
        else:
            flash('Horário não encontrado.', 'danger')
            
        return redirect(url_for('horario.aprovar_horarios'))
        
    aulas_pendentes = db.session.scalars(
        select(Horario).where(Horario.status == 'pendente').order_by(Horario.id)
    ).all()
    
    return render_template('aprovar_horarios.html', aulas_pendentes=aulas_pendentes)