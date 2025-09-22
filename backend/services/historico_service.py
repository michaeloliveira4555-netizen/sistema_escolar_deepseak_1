# backend/services/historico_service.py

from ..models.database import db
from ..models.aluno import Aluno
from ..models.disciplina import Disciplina
from ..models.historico_disciplina import HistoricoDisciplina
from ..models.historico import HistoricoAluno
from sqlalchemy import select, and_
from flask import current_app

class HistoricoService:

    @staticmethod
    def get_historico_disciplinas_for_aluno(aluno_id: int):
        """
        Busca todos os registros de disciplinas (matrículas) para um aluno específico.
        """
        stmt = select(HistoricoDisciplina).where(HistoricoDisciplina.aluno_id == aluno_id).order_by(HistoricoDisciplina.id)
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_historico_atividades_for_aluno(aluno_id: int):
        """
        Busca todos os registros de atividades (ex: mudanças de perfil) para um aluno específico.
        """
        stmt = select(HistoricoAluno).where(HistoricoAluno.aluno_id == aluno_id).order_by(HistoricoAluno.data_inicio.desc())
        return db.session.scalars(stmt).all()

    @staticmethod
    def avaliar_aluno(historico_id: int, form_data: dict):
        """
        Lança ou atualiza as notas de um aluno em uma disciplina e calcula a média final.
        """
        registro = db.session.get(HistoricoDisciplina, historico_id)
        if not registro:
            return False, "Registro de matrícula não encontrado.", None

        try:
            # Converte notas para float, tratando campos vazios como None
            nota_p1 = float(form_data.get('nota_p1')) if form_data.get('nota_p1') else None
            nota_p2 = float(form_data.get('nota_p2')) if form_data.get('nota_p2') else None
            nota_rec = float(form_data.get('nota_rec')) if form_data.get('nota_rec') else None

            registro.nota_p1 = nota_p1
            registro.nota_p2 = nota_p2
            registro.nota_rec = nota_rec

            # Lógica de cálculo da nota final (MPD/MFD)
            if nota_p1 is not None and nota_p2 is not None:
                mpd = (nota_p1 + nota_p2) / 2
                if mpd < 7.0 and nota_rec is not None:
                    # MFD (Média Final da Disciplina)
                    mfd = (nota_p1 + nota_p2 + nota_rec) / 3
                    registro.nota = round(mfd, 3)
                else:
                    # MPD (Média Parcial da Disciplina)
                    registro.nota = round(mpd, 3)
            else:
                registro.nota = None # Se não houver notas P1 e P2, a média final é nula

            db.session.commit()
            return True, "Avaliação salva com sucesso.", registro.aluno_id
        except (ValueError, TypeError):
            db.session.rollback()
            return False, "As notas devem ser números válidos.", registro.aluno_id
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar avaliação: {e}")
            return False, "Ocorreu um erro ao salvar a avaliação.", registro.aluno_id