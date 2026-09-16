from sqlalchemy import text

from database import db


class AvaliacaoRepository:
    """Leitura das avaliações de um chamado. A consulta com JOIN (avaliação +
    nome do autor e do avaliado) vive na procedure
    fn_listar_avaliacoes_por_servico — antes este caminho era o único do
    projeto que ia direto ao ORM e resolvia os dois nomes com lazy load,
    uma consulta extra por linha."""

    def listar_por_servico(self, servico_id):
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_avaliacoes_por_servico(:servico_id)"),
            {"servico_id": servico_id},
        )
        return [linha[0] for linha in resultado]
