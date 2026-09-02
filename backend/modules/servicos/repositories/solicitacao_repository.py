from sqlalchemy import text

from database import db


class SolicitacaoRepository:
    """Consultas de SolicitacaoTecnico que extrapolam CRUD simples (JOIN
    com o servico e o cliente) — usado pela área "Solicitações pendentes"
    do painel do técnico. A consulta com JOIN vive na procedure
    fn_listar_solicitacoes_pendentes (ver backend/database/procedures.sql);
    este Repository só chama e repassa o resultado, sem Model/SQLAlchemy
    ORM direto."""

    def buscar_pendentes_com_detalhes(self, tecnico_id):
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_solicitacoes_pendentes(:tecnico_id)"),
            {"tecnico_id": tecnico_id},
        )
        return [linha[0] for linha in resultado]
