from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import date 

from ..models.database import db
from ..models.horario import Horario
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.semana import Semana
from ..models.turma import Turma
from ..services.disciplina_service import DisciplinaService
from utils.decorators import admin_or_programmer_required

# --- LINHA MOVIDA PARA CIMA ---
horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

@horario_bp.route('/')
@login_required
def index():
    todas_as_turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()
    todas_as_semanas = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()

    if not todas_as_turmas or not todas_as_semanas:
        flash('Cadastre ao menos uma turma e uma semana para visualizar o horário.', 'warning')
        return redirect(url_for('main.dashboard'))

    turma_selecionada_nome = request.args.get('pelotao', session.get('ultima_turma_visualizada', todas_as_turmas[0].nome if todas_as_turmas else ''))
    
    semana_id_selecionada = request.args.get('semana_id')
    if semana_id_selecionada:
        semana_selecionada = db.session.get(Semana, int(semana_id_selecionada))
    else:
        today = date.today()
        semana_selecionada = db.session.scalars(
            select(Semana).where(Semana.data_inicio <= today, Semana.data_fim >= today)
        ).first()
        if not semana_selecionada:
            semana_selecionada = todas_as_semanas[0] if todas_as_semanas else None

    if not semana_selecionada:
         flash('Nenhuma semana encontrada. Por favor, cadastre uma semana.', 'warning')
         return redirect(url_for('main.dashboard'))

    session['ultima_turma_visualizada'] = turma_selecionada_nome

    horario_matrix = construir_matriz_horario(turma_selecionada_nome, semana_selecionada.id)
    
    return render_template('quadro_horario.html', 
                           horario_matrix=horario_matrix, 
                           pelotao_selecionado=turma_selecionada_nome, 
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=todas_as_turmas,
                           todas_as_semanas=todas_as_semanas)

@horario_bp.route('/editar/<pelotao>/<int:semana_id>')
@login_required
def editar_horario_grid(pelotao, semana_id):
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana não encontrada.", "danger")
        return redirect(url_for('horario.index'))

    is_admin = current_user.role in ['admin', 'programador']
    instrutor_id = current_user.instrutor_profile.id if current_user.instrutor_profile else None

    if not is_admin and not instrutor_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('horario.index'))

    horario_matrix = construir_matriz_horario(pelotao, semana_id)
    
    associacoes = DisciplinaService.get_disciplinas_with_instrutores_for_pelotao(pelotao)

    if not is_admin:
        associacoes = [
            a for a in associacoes 
            if a.instrutor_id_1 == instrutor_id or a.instrutor_id_2 == instrutor_id
        ]

    disciplinas_disponiveis = []
    for a in associacoes:
        total_previsto = a.disciplina.carga_horaria_prevista
        horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(
            disciplina_id=a.disciplina.id, 
            pelotao=pelotao,
            status='confirmado'
        ).scalar() or 0
        
        instrutor1_nome = None
        if a.instrutor_1 and a.instrutor_1.user:
            instrutor1_nome = a.instrutor_1.user.nome_completo or a.instrutor_1.user.username

        instrutor2_nome = None
        if a.instrutor_2 and a.instrutor_2.user:
            instrutor2_nome = a.instrutor_2.user.nome_completo or a.instrutor_2.user.username

        disciplinas_disponiveis.append({
            "id": a.disciplina.id,
            "nome": a.disciplina.materia,
            "instrutor_id": a.instrutor_id_1,
            "instrutor_nome": instrutor1_nome,
            "instrutor_id_2": a.instrutor_id_2,
            "instrutor_nome_2": instrutor2_nome,
            "carga_total": total_previsto,
            "carga_feita": horas_agendadas,
            "carga_restante": total_previsto - horas_agendadas
        })

    return render_template(
        'editar_quadro_horario.html', 
        horario_matrix=horario_matrix, 
        pelotao_selecionado=pelotao,
        semana_selecionada=semana,
        disciplinas_disponiveis=disciplinas_disponiveis,
        is_admin=is_admin
    )

@horario_bp.route('/get-aula/<int:horario_id>')
@login_required
def get_aula_details(horario_id):
    aula = db.session.get(Horario, horario_id)
    if not aula:
        return jsonify({'success': False, 'message': 'Aula não encontrada'}), 404
    
    return jsonify({
        'success': True,
        'disciplina_id': aula.disciplina_id,
        'instrutor_id': aula.instrutor_id,
        'duracao': aula.duracao
    })

@horario_bp.route('/salvar-aula', methods=['POST'])
@login_required
def salvar_aula():
    data = request.json
    horario_id = data.get('horario_id')

    if not data.get('disciplina_id') or not data.get('instrutor_id'):
        return jsonify({'success': False, 'message': 'Disciplina e Instrutor são obrigatórios.'}), 400

    try:
        if horario_id:
            aula = db.session.get(Horario, int(horario_id))
            if not aula:
                return jsonify({'success': False, 'message': 'Aula não encontrada.'}), 404
        else:
            aula = Horario(
                pelotao=data.get('pelotao'),
                semana_id=int(data.get('semana_id')),
                dia_semana=data.get('dia'),
                periodo=int(data.get('periodo'))
            )
            db.session.add(aula)

        aula.disciplina_id = int(data.get('disciplina_id'))
        aula.instrutor_id = int(data.get('instrutor_id'))
        aula.duracao = int(data.get('duracao', 1))
        aula.status = 'confirmado' if current_user.role in ['admin', 'programador'] else 'pendente'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aula salva com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar aula: {e}")
        return jsonify({'success': False, 'message': 'Ocorreu um erro ao salvar a aula.'}), 500

@horario_bp.route('/remover-aula', methods=['POST'])
@login_required
def remover_aula():
    data = request.json
    horario_id = data.get('horario_id')

    try:
        aula = db.session.get(Horario, int(horario_id))
        if aula:
            db.session.delete(aula)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Aula removida com sucesso!'})
        return jsonify({'success': False, 'message': 'Aula não encontrada.'}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover aula: {e}")
        return jsonify({'success': False, 'message': 'Ocorreu um erro ao remover a aula.'}), 500

@horario_bp.route('/aprovar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def aprovar_horarios():
    if request.method == 'POST':
        horario_id = request.form.get('horario_id')
        action = request.form.get('action')
        
        horario = db.session.get(Horario, int(horario_id))
        
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

def construir_matriz_horario(pelotao, semana_id):
    a_disposicao = {'materia': 'A disposição do C Al /S Ens', 'instrutor': None, 'duracao': 1, 'is_disposicao': True, 'id': None}
    horario_matrix = [[dict(a_disposicao) for _ in range(7)] for _ in range(15)]
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
                    'id': aula.id,
                    'materia': aula.disciplina.materia,
                    'instrutor': instrutor_nome, 
                    'duracao': aula.duracao,
                    'status': aula.status, 
                    'is_disposicao': False,
                }
                horario_matrix[periodo_idx][dia_idx] = aula_info
                
                for i in range(1, aula.duracao):
                    if periodo_idx + i < 15:
                        horario_matrix[periodo_idx + i][dia_idx] = 'SKIP'
        except (ValueError, IndexError):
            continue
    return horario_matrix