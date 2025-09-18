from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import date
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired

from ..models.database import db
from ..models.horario import Horario
from ..models.disciplina import Disciplina
from ..models.instrutor import Instrutor
from ..models.disciplina_turma import DisciplinaTurma
from ..models.semana import Semana
from ..models.turma import Turma
from utils.decorators import admin_or_programmer_required
from ..services.horario_service import HorarioService

horario_bp = Blueprint('horario', __name__, url_prefix='/horario')

# Forms
class AprovarHorarioForm(FlaskForm):
    horario_id = HiddenField('Horário ID', validators=[DataRequired()])
    action = HiddenField('Ação', validators=[DataRequired()]) # 'aprovar' ou 'rejeitar'
    submit = SubmitField('Enviar')

@horario_bp.route('/')
@login_required
def index():
    ciclo_selecionado = request.args.get('ciclo', session.get('ultimo_ciclo_horario', 1), type=int)
    session['ultimo_ciclo_horario'] = ciclo_selecionado

    todas_as_turmas = []
    if current_user.role == 'instrutor':
        if not current_user.instrutor_profile:
            flash('Perfil de instrutor não configurado.', 'warning')
            return redirect(url_for('main.dashboard'))

        vinculos = DisciplinaTurma.query.filter(
            (DisciplinaTurma.instrutor_id_1 == current_user.instrutor_profile.id) |
            (DisciplinaTurma.instrutor_id_2 == current_user.instrutor_profile.id)
        ).all()
        
        if not vinculos:
            flash('Você não está vinculado a nenhuma turma ou disciplina.', 'warning')
            return redirect(url_for('main.dashboard'))

        nomes_turmas_instrutor = sorted(list(set([v.pelotao for v in vinculos])))
        
        todas_as_turmas = db.session.scalars(
            select(Turma).where(Turma.nome.in_(nomes_turmas_instrutor)).order_by(Turma.nome)
        ).all()

        if len(nomes_turmas_instrutor) == 1:
            semana_id = request.args.get('semana_id')
            return redirect(url_for('horario.index_com_turma', pelotao=nomes_turmas_instrutor[0], semana_id=semana_id, ciclo=ciclo_selecionado))
    else:
        todas_as_turmas = db.session.scalars(select(Turma).order_by(Turma.nome)).all()

    todas_as_semanas = db.session.scalars(select(Semana).where(Semana.ciclo == ciclo_selecionado).order_by(Semana.data_inicio.desc())).all()
    datas_semana = {} # GARANTE QUE A VARIÁVEL SEMPRE EXISTA

    if not todas_as_turmas or not todas_as_semanas:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=None,
                               semana_selecionada=None,
                               todas_as_turmas=todas_as_turmas,
                               todas_as_semanas=todas_as_semanas,
                               ciclos=[1, 2, 3],
                               ciclo_selecionado=ciclo_selecionado,
                               datas_semana=datas_semana)

    turma_selecionada_nome = request.args.get('pelotao', session.get('ultima_turma_visualizada'))
    if not turma_selecionada_nome and todas_as_turmas:
        turma_selecionada_nome = todas_as_turmas[0].nome

    semana_id_selecionada = request.args.get('semana_id')
    semana_selecionada = None
    if semana_id_selecionada:
        semana_selecionada = db.session.get(Semana, int(semana_id_selecionada))

    if not semana_selecionada:
        today = date.today()
        semana_selecionada = db.session.scalars(
            select(Semana).where(Semana.ciclo == ciclo_selecionado, Semana.data_inicio <= today, Semana.data_fim >= today)
        ).first()
        if not semana_selecionada and todas_as_semanas:
            semana_selecionada = todas_as_semanas[0]

    if not semana_selecionada:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=turma_selecionada_nome,
                               semana_selecionada=None,
                               todas_as_turmas=todas_as_turmas,
                               todas_as_semanas=todas_as_semanas)


    session['ultima_turma_visualizada'] = turma_selecionada_nome

    horario_matrix = HorarioService.construir_matriz_horario(turma_selecionada_nome, semana_selecionada.id)

    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=turma_selecionada_nome,
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=todas_as_turmas,
                           todas_as_semanas=todas_as_semanas,
                           ciclos=[1, 2, 3],
                           ciclo_selecionado=ciclo_selecionado,
                           datas_semana=datas_semana)

@horario_bp.route('/<pelotao>')
@login_required
def index_com_turma(pelotao):
    ciclo_selecionado = request.args.get('ciclo', session.get('ultimo_ciclo_horario', 1), type=int)
    session['ultimo_ciclo_horario'] = ciclo_selecionado
    
    todas_as_semanas = db.session.scalars(select(Semana).where(Semana.ciclo == ciclo_selecionado).order_by(Semana.data_inicio.desc())).all()
    datas_semana = {} # GARANTE QUE A VARIÁVEL SEMPRE EXISTA
    
    semana_id_selecionada = request.args.get('semana_id')
    semana_selecionada = None
    if semana_id_selecionada and semana_id_selecionada != 'None':
        semana_selecionada = db.session.get(Semana, int(semana_id_selecionada))
    else:
        today = date.today()
        semana_selecionada = db.session.scalars(
            select(Semana).where(Semana.ciclo == ciclo_selecionado, Semana.data_inicio <= today, Semana.data_fim >= today)
        ).first()
        if not semana_selecionada and todas_as_semanas:
            semana_selecionada = todas_as_semanas[0]
    
    if semana_selecionada:
        horario_matrix = construir_matriz_horario(pelotao, semana_selecionada.id, ciclo_selecionado)
        dia_atual = semana_selecionada.data_inicio
        dias_da_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        for i in range(7):
            datas_semana[dias_da_semana[i]] = (dia_atual + timedelta(days=i)).strftime('%d/%m')
    else:
        horario_matrix = None


    if not semana_selecionada:
        return render_template('quadro_horario.html',
                               horario_matrix=None,
                               pelotao_selecionado=pelotao,
                               semana_selecionada=None,
                               todas_as_turmas=[db.session.query(Turma).filter_by(nome=pelotao).first()],
                               todas_as_semanas=todas_as_semanas)

    horario_matrix = HorarioService.construir_matriz_horario(pelotao, semana_selecionada.id)
    turma_atual = db.session.query(Turma).filter_by(nome=pelotao).first()

    return render_template('quadro_horario.html',
                           horario_matrix=horario_matrix,
                           pelotao_selecionado=pelotao,
                           semana_selecionada=semana_selecionada,
                           todas_as_turmas=turmas_visiveis,
                           todas_as_semanas=todas_as_semanas,
                           ciclos=[1, 2, 3],
                           ciclo_selecionado=ciclo_selecionado,
                           datas_semana=datas_semana)

@horario_bp.route('/editar/<pelotao>/<int:semana_id>/<int:ciclo_id>')
@login_required
def editar_horario_grid(pelotao, semana_id, ciclo_id):
    semana = db.session.get(Semana, semana_id)
    if not semana:
        flash("Semana não encontrada.", "danger")
        return redirect(url_for('horario.index'))

    is_admin = current_user.role in ['super_admin', 'programador']
    instrutor_id = current_user.instrutor_profile.id if hasattr(current_user, 'instrutor_profile') and current_user.instrutor_profile else None

    if not is_admin and not instrutor_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('horario.index'))

    horario_matrix = HorarioService.construir_matriz_horario(pelotao, semana_id)

    disciplinas_disponiveis = []
    todos_instrutores = []
    disciplinas_do_ciclo = db.session.scalars(select(Disciplina).where(Disciplina.ciclo == ciclo_id).order_by(Disciplina.materia)).all()

    if is_admin:
        todos_instrutores_query = db.session.scalars(select(Instrutor).options(joinedload(Instrutor.user)).order_by(Instrutor.id)).all()

        for inst in todos_instrutores_query:
            nome = "Sem nome"
            if inst.user:
                nome = inst.user.nome_completo or inst.user.username or f"User {inst.user.id}"
            todos_instrutores.append({"id": inst.id, "nome": nome})

        for disciplina in disciplinas_do_ciclo:
            total_previsto = disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(disciplina_id=disciplina.id, pelotao=pelotao, status='confirmado').scalar() or 0
            disciplinas_disponiveis.append({
                "id": disciplina.id,
                "nome": disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas)
            })
    else: 
        ids_disciplinas_ciclo = {d.id for d in disciplinas_do_ciclo}
        associacoes_query = (
            select(DisciplinaTurma).options(joinedload(DisciplinaTurma.disciplina))
            .where(
                DisciplinaTurma.pelotao == pelotao, 
                (DisciplinaTurma.instrutor_id_1 == instrutor_id) | (DisciplinaTurma.instrutor_id_2 == instrutor_id),
                DisciplinaTurma.disciplina_id.in_(ids_disciplinas_ciclo)
            )
            .order_by(DisciplinaTurma.disciplina_id)
        )
        associacoes = db.session.scalars(associacoes_query).unique().all()
        for a in associacoes:
            total_previsto = a.disciplina.carga_horaria_prevista or 0
            horas_agendadas = db.session.query(func.sum(Horario.duracao)).filter_by(disciplina_id=a.disciplina.id, pelotao=pelotao, status='confirmado').scalar() or 0
            disciplinas_disponiveis.append({
                "id": a.disciplina.id,
                "nome": a.disciplina.materia,
                "carga_total": total_previsto,
                "carga_feita": horas_agendadas,
                "carga_restante": max(0, total_previsto - horas_agendadas),
                "instrutor_automatico": instrutor_id
            })
    
    datas_semana = {}
    dia_atual = semana.data_inicio
    dias_da_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
    for i in range(7):
        datas_semana[dias_da_semana[i]] = (dia_atual + timedelta(days=i)).strftime('%d/%m')

    return render_template(
        'editar_quadro_horario.html',
        horario_matrix=horario_matrix,
        pelotao_selecionado=pelotao,
        semana_selecionada=semana,
        disciplinas_disponiveis=disciplinas_disponiveis,
        todos_instrutores=todos_instrutores,
        is_admin=is_admin,
        instrutor_logado_id=instrutor_id,
        datas_semana=datas_semana
    )

@horario_bp.route('/get-aula/<int:horario_id>')
@login_required
def get_aula_details(horario_id):
    if not HorarioService.can_edit_horario(horario_id):
        return jsonify({'success': False, 'message': 'Acesso negado. Você não pode editar esta aula.'}), 403
    aula = db.session.get(Horario, horario_id)
    if not aula:
        return jsonify({'success': False, 'message': 'Aula não encontrada'}), 404
    return jsonify({'success': True, 'disciplina_id': aula.disciplina_id, 'instrutor_id': aula.instrutor_id, 'duracao': aula.duracao})

@horario_bp.route('/salvar-aula', methods=['POST'])
@login_required
def salvar_aula():
    data = request.json
    is_admin = current_user.role in ['super_admin', 'programador']
    semana_id = int(data.get('semana_id'))
    semana = db.session.get(Semana, semana_id)
    if not semana:
        return jsonify({'success': False, 'message': 'Semana não encontrada.'}), 404
        
    if not is_admin:
        dia = data.get('dia')
        periodo = int(data.get('periodo'))

        if dia == 'sabado' and not semana.mostrar_sabado:
            return jsonify({'success': False, 'message': 'Agendamento no Sábado não está habilitado para esta semana.'}), 403
        if dia == 'domingo' and not semana.mostrar_domingo:
            return jsonify({'success': False, 'message': 'Agendamento no Domingo não está habilitado para esta semana.'}), 403
        
        if periodo == 13 and not semana.mostrar_periodo_13:
             return jsonify({'success': False, 'message': 'Agendamento no 13º período não está habilitado.'}), 403
        if periodo == 14 and not semana.mostrar_periodo_14:
             return jsonify({'success': False, 'message': 'Agendamento no 14º período não está habilitado.'}), 403
        if periodo == 15 and not semana.mostrar_periodo_15:
             return jsonify({'success': False, 'message': 'Agendamento no 15º período não está habilitado.'}), 403

        if dia == 'sabado' and periodo > semana.periodos_sabado:
            return jsonify({'success': False, 'message': f'Apenas {semana.periodos_sabado} períodos estão disponíveis no Sábado.'}), 403
        if dia == 'domingo' and periodo > semana.periodos_domingo:
            return jsonify({'success': False, 'message': f'Apenas {semana.periodos_domingo} períodos estão disponíveis no Domingo.'}), 403
    
    horario_id = data.get('horario_id')
    if not data.get('disciplina_id'):
        return jsonify({'success': False, 'message': 'Disciplina é obrigatória.'}), 400
    
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
    success, message = HorarioService.remove_aula(horario_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 403

@horario_bp.route('/aprovar', methods=['GET', 'POST'])
@login_required
@admin_or_programmer_required
def aprovar_horarios():
    form = AprovarHorarioForm()
    if form.validate_on_submit():
        horario_id = form.horario_id.data
        action = form.action.data
        success, message = HorarioService.aprovar_horario(horario_id, action)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('horario.aprovar_horarios'))
    aulas_pendentes = db.session.scalars(select(Horario).options(joinedload(Horario.disciplina)).where(Horario.status == 'pendente').order_by(Horario.id)).all()
    return render_template('aprovar_horarios.html', aulas_pendentes=aulas_pendentes)

def construir_matriz_horario(pelotao, semana_id, ciclo):
    a_disposicao = {'materia': 'A disposição do C Al /S Ens', 'instrutor': None, 'duracao': 1, 'is_disposicao': True, 'id': None}
    horario_matrix = [[dict(a_disposicao) for _ in range(7)] for _ in range(15)]
    dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
    
    aulas_agendadas = db.session.scalars(
        select(Horario).options(joinedload(Horario.disciplina), joinedload(Horario.instrutor).joinedload(Instrutor.user))
        .join(Disciplina)
        .where(
            Horario.pelotao == pelotao, 
            Horario.semana_id == semana_id,
            Disciplina.ciclo == ciclo
        )
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

