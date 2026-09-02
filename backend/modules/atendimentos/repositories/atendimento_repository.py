from sqlalchemy import text

from database import db


class AtendimentoRepository:
    """Consultas de Atendimento (orçamento) que extrapolam CRUD simples —
    usado pela tela do cliente que compara os orçamentos recebidos pra um
    chamado, e precisa do nome/avaliação do técnico junto com cada um. A
    consulta com JOIN vive na procedure fn_listar_orcamentos_por_servico
    (ver backend/database/procedures.sql); este Repository só chama e
    repassa o resultado, sem Model/SQLAlchemy ORM direto."""

    def listar_por_servico_com_tecnico(self, servico_id):
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_orcamentos_por_servico(:servico_id)"),
            {"servico_id": servico_id},
        )
        return [linha[0] for linha in resultado]
