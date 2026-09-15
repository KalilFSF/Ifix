from sqlalchemy import text

from database import db


class AprovacaoRepository:
    """Autorizações de custo adicional de um chamado, com o nome do técnico
    que pediu junto de cada uma. O JOIN vive na procedure
    fn_listar_aprovacoes_por_servico (ver backend/database/procedures.sql);
    este Repository só chama e repassa o resultado, sem Model/ORM direto."""

    def listar_por_servico(self, servico_id):
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_aprovacoes_por_servico(:servico_id)"),
            {"servico_id": servico_id},
        )
        return [linha[0] for linha in resultado]
