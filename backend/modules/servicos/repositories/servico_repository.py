from sqlalchemy import text

from database import db


class ServicoRepository:
    """Consultas de Servico que extrapolam CRUD simples (JOIN com os
    participantes) — usado pelo painel do técnico e por "Acompanhar
    chamado" do cliente, que precisam do nome/telefone de cliente e
    técnico junto com cada chamado. A consulta com JOIN vive na procedure
    fn_listar_servicos_participante (ver backend/database/procedures.sql);
    este Repository só chama e repassa o resultado, sem Model/SQLAlchemy
    ORM direto."""

    def buscar_meus_com_participantes(self, usuario_id, como, status=None):
        # `como` escolhe o modo da listagem (cliente = abertos por mim;
        # tecnico = que eu atendo), independente do role da conta.
        resultado = db.session.execute(
            text("SELECT * FROM fn_listar_servicos_participante(:usuario_id, :como, :status)"),
            {"usuario_id": usuario_id, "como": como, "status": status},
        )
        return [linha[0] for linha in resultado]

    def buscar_historico_aparelho(self, cliente_id, equipamento, excluir_servico_id=None):
        """Chamados anteriores do mesmo cliente para o mesmo aparelho
        (funcionalidade 10) — procedure fn_historico_aparelho."""
        resultado = db.session.execute(
            text("SELECT * FROM fn_historico_aparelho(:cliente_id, :equipamento, CAST(:excluir_id AS integer))"),
            {"cliente_id": cliente_id, "equipamento": equipamento, "excluir_id": excluir_servico_id},
        )
        return [linha[0] for linha in resultado]
