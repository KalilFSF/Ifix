from sqlalchemy.orm import contains_eager

from database import db
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class SolicitacaoRepository:
    """Consultas de SolicitacaoTecnico que extrapolam CRUD simples (JOIN
    com o servico e o cliente) — usado pela área "Solicitações pendentes"
    do painel do técnico."""

    def buscar_pendentes_com_detalhes(self, tecnico_id):
        return (
            db.session.query(SolicitacaoTecnico)
            .join(SolicitacaoTecnico.servico)
            .join(Servico.cliente)
            .options(contains_eager(SolicitacaoTecnico.servico).contains_eager(Servico.cliente))
            .filter(SolicitacaoTecnico.tecnico_id == tecnico_id, SolicitacaoTecnico.status == "pendente")
            .order_by(SolicitacaoTecnico.criado_em.desc())
            .all()
        )
