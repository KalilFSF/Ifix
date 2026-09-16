from sqlalchemy import text

from database import db


class MensagemRepository:
    """Leitura do chat. A consulta com JOIN (mensagem + nome do autor) vive
    na procedure fn_listar_mensagens_chamado, em
    backend/database/procedures.sql — este Repository só chama e repassa,
    como os demais."""

    def listar_por_servico(self, servico_id, desde_id=None):
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_mensagens_chamado(:servico_id, :desde_id)"),
            {"servico_id": servico_id, "desde_id": desde_id},
        )
        return [linha[0] for linha in resultado]

    def contar_nao_lidas_por_servico(self, usuario_id):
        """{servico_id: quantidade} das mensagens que chegaram pro usuário e
        ainda não foram lidas — alimenta o badge dos dois painéis com uma
        chamada só, em vez de uma por chamado aberto na tela."""
        resultado = db.session.execute(
            text("SELECT * FROM fn_contar_mensagens_nao_lidas(:usuario_id)"),
            {"usuario_id": usuario_id},
        )
        return {linha["servico_id"]: linha["nao_lidas"] for linha in resultado.mappings()}
