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
from utils.decorators import admin_or_programmer_required

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

def can_edit_horario(horario_id):
    """Verifica se o usuário atual pode editar/deletar um horário específico"""
    if current_user.role in ['admin', 'programador']:
        return True

    if current_user.role == 'instrutor' and current_user.instrutor_profile:
        horario = db.session.get(Horario, horario_id)
        if horario and horario.instrutor_id == current_user.instrutor_profile.id:
            return True

    return False

@horario_bp.route('/')
@login_required
def index():
    # Lógica para instrutor
    if current_user.role == 'instrutor':
        # Verifica se o instrutor tem um perfil, senão não pode ter vínculos
        if not current_user.instrutor_profile:
            flash('Perfil de instrutor não configurado.', 'warning')
            return redirect(url_for('main.dashboard'))

        vinculos = DisciplinaTurma.query.filter_by(instrutor_id_1=current_user.instrutor_profile.id).all()
        if not vinculos:
            flash('Você não está vinculado a nenhuma turma ou disciplina.', 'warning')
            return redirect(url_for('main.dashboard'))

        turmas_instrutor = list(set([v.pelotao for v in vinculos]))
        if len(turmas_instrutor) == 1:
            # **CORREÇÃO APLICADA AQUI**
            # Pega o ID da semana da URL e o repassa no redirecionamento.
            semana_id = request.args.get('semana_id')
            return redirect(url_for('horario.index_com_turma', pelotao=turmas_instrutor[0], semana_id=semana_id))

    # Lógica para admin/programador ou instrutor com múltiplas turmas
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

@horario_bp.route('/<pelotao>')
@login_required
def index_com_turma(pelotao):
    # Rota para instrutores com apenas uma turma
    todas_as_semanas = db.session.scalars(select(Semana).order_by(Semana.data_inicio.desc())).all()

    semana_id_selecionada = request.args.get('semana_id')
    if semana_id_selecionada and semana_id_selecionada != 'None':
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

    horario_matrix = construir_matriz_horario(pelotao, semana_selecionada.id)
    
    turma_atual = db.session.query(Turma).filter_by(nome=pelotao).first()
    todas_as_turmas = [turma_atual] if turma_atual else []


    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=pelotao,
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
    instrutor_id = current_user.instrutor_profile.id if hasattr(current_user, 'instrutor_profile') and current_user.instrutor_profile else None

    if not is_admin and not instrutor_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('horario.index'))

    horario_matrix = construir_matriz_horario(pelotao, semana_id)

    disciplinas_disponiveis = []
    todos_instrutores = []

    if is_admin:
        todas_disciplinas = db.session.scalars(
            select(Disciplina).order_by(Disciplina.materia)
        ).all()
        
        todos_instrutores_query = db.session.scalars(
            select(Instrutor)
            .options(joinedload(Instrutor.user))
            .order_by(Instrutor.id)
        ).all()
        
        for inst in todos_instrutores_query:
            nome = "Sem nome"
            if inst.user:
                nome = inst.user.nome_completo or inst.user.username or f"User {inst.user.id}"
            todos_instrutores.append({
                "id": inst.id,
                "nome": nome
            })
        
        for disciplina in todas_disciplinas:
            total_previsto = disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(
                disciplina_id=disciplina.id, 
                pelotao=pelotao,
                status='confirmado'
            ).scalar() or 0
            
            disciplinas_disponiveis.append({
                "id": disciplina.id,
                "nome": disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas)
            })
    else:
        associacoes_query = (
            select(DisciplinaTurma)
            .options(joinedload(DisciplinaTurma.disciplina))
            .where(
                DisciplinaTurma.pelotao == pelotao,
                (DisciplinaTurma.instrutor_id_1 == instrutor_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_id)
            )
            .order_by(DisciplinaTurma.disciplina_id)
        )
        
        associacoes = db.session.scalars(associacoes_query).unique().all()
        
        for a in associacoes:
            total_previsto = a.disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(
                disciplina_id=a.disciplina.id, 
                pelotao=pelotao,
                status='confirmado'
            ).scalar() or 0
            
            disciplinas_disponiveis.append({
                "id": a.disciplina.id,
                "nome": a.disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas),
                "instrutor_automatico": instrutor_id
            })

    return render_template(
        'editar_quadro_horario.html', 
        horario_matrix=horario_matrix, 
        pelotao_selecionado=pelotao,
        semana_selecionada=semana,
        disciplinas_disponiveis=disciplinas_disponiveis,
        todos_instrutores=todos_instrutores,
        is_admin=is_admin,
        instrutor_logado_id=instrutor_id
    )

@horario_bp.route('/get-aula/<int:horario_id>')
@login_required
def get_aula_details(horario_id):
    if not can_edit_horario(horario_id):
        return jsonify({'success': False, 'message': 'Acesso negado. Você não pode editar esta aula.'}), 403
    
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

    if not data.get('disciplina_id'):
        return jsonify({'success': False, 'message': 'Disciplina é obrigatória.'}), 400

    is_admin = current_user.role in ['admin', 'programador']
    
    if is_admin:
        if not data.get('instrutor_id'):
            return jsonify({'success': False, 'message': 'Instrutor é obrigatório para administradores.'}), 400
        instrutor_final_id = int(data.get('instrutor_id'))
    else:
        if not current_user.instrutor_profile:
            return jsonify({'success': False, 'message': 'Usuário não é um instrutor válido.'}), 400
        instrutor_final_id = current_user.instrutor_profile.id

    disciplina = db.session.get(Disciplina, int(data.get('disciplina_id')))
    if not disciplina:
        return jsonify({'success': False, 'message': 'Disciplina não encontrada.'}), 400

    instrutor = db.session.get(Instrutor, instrutor_final_id)
    if not instrutor:
        return jsonify({'success': False, 'message': 'Instrutor não encontrado.'}), 400

    if not is_admin:
        pelotao = data.get('pelotao')
        associacao = db.session.execute(
            select(DisciplinaTurma).where(
                DisciplinaTurma.pelotao == pelotao,
                DisciplinaTurma.disciplina_id == disciplina.id,
                (DisciplinaTurma.instrutor_id_1 == instrutor_final_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_final_id)
            )
        ).scalar_one_or_none()
        
        if not associacao:
            return jsonify({'success': False, 'message': 'Você não está autorizado para esta disciplina neste pelotão.'}), 400

    try:
        if horario_id:
            if not can_edit_horario(int(horario_id)):
                return jsonify({'success': False, 'message': 'Acesso negado. Você não pode editar esta aula.'}), 403
            
            aula = db.session.get(Horario, int(horario_id))
            if not aula:
                return jsonify({'success': False, 'message': 'Aula não encontrada.'}), 404
            
            aula.disciplina_id = int(data.get('disciplina_id'))
            aula.instrutor_id = instrutor_final_id
            aula.duracao = int(data.get('duracao', 1))
            aula.status = 'confirmado' if is_admin else 'pendente'
            
        else:
            conflito = db.session.execute(
                select(Horario).where(
                    Horario.pelotao == data.get('pelotao'),
                    Horario.semana_id == int(data.get('semana_id')),
                    Horario.dia_semana == data.get('dia'),
                    Horario.periodo == int(data.get('periodo'))
                )
            ).scalar_one_or_none()
            
            if conflito:
                return jsonify({'success': False, 'message': 'Já existe uma aula agendada neste horário.'}), 400
            
            aula = Horario()
            
            aula.pelotao = data.get('pelotao')
            aula.semana_id = int(data.get('semana_id'))
            aula.dia_semana = data.get('dia')
            aula.periodo = int(data.get('periodo'))
            aula.disciplina_id = int(data.get('disciplina_id'))
            aula.instrutor_id = instrutor_final_id
            aula.duracao = int(data.get('duracao', 1))
            aula.status = 'confirmado' if is_admin else 'pendente'
            
            db.session.add(aula)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aula salva com sucesso!'})
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Dados inválidos fornecidos.'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar aula: {e}")
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@horario_bp.route('/remover-aula', methods=['POST'])
@login_required
def remover_aula():
    data = request.json
    horario_id = data.get('horario_id')

    if not can_edit_horario(int(horario_id)):
        return jsonify({'success': False, 'message': 'Acesso negado. Você não pode remover esta aula.'}), 403

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
        select(Horario)
        .options(
            joinedload(Horario.disciplina),
            joinedload(Horario.instrutor).joinedload(Instrutor.user)
        )
        .where(Horario.pelotao == pelotao, Horario.semana_id == semana_id)
    ).all()

    for aula in aulas_agendadas:
        try:
            dia_idx = dias.index(aula.dia_semana)
            periodo_idx = aula.periodo - 1
            if 0 <= periodo_idx < 15 and 0 <= dia_idx < 7:
                instrutor_nome = "N/D"
                if aula.instrutor and aula.instrutor.user:
                    instrutor_nome = aula.instrutor.user.nome_completo or aula.instrutor.user.username
                
                can_edit = can_edit_horario(aula.id)
                
                aula_info = {
                    'id': aula.id,
                    'materia': aula.disciplina.materia,
                    'instrutor': instrutor_nome, 
                    'duracao': aula.duracao,
                    'status': aula.status, 
                    'is_disposicao': False,
                    'can_edit': can_edit,
                }
                horario_matrix[periodo_idx][dia_idx] = aula_info
                
                for i in range(1, aula.duracao):
                    if periodo_idx + i < 15:
                        horario_matrix[periodo_idx + i][dia_idx] = 'SKIP'
        except (ValueError, IndexError):
            continue
    return horario_matrix