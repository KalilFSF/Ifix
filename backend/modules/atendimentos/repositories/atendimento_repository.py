from sqlalchemy.orm import contains_eager

from database import db
from modules.atendimentos.models.atendimento import Atendimento
from modules.usuarios.models.usuario import Usuario


class AtendimentoRepository:
    """Consultas de Atendimento (orçamento) que extrapolam CRUD simples —
    usado pela tela do cliente que compara os orçamentos recebidos pra um
    chamado, e precisa do nome/avaliação do técnico junto com cada um sem
    N+1 query por linha."""

    def listar_por_servico_com_tecnico(self, servico_id):
        return (
            db.session.query(Atendimento)
            .join(Usuario, Atendimento.tecnico_id == Usuario.id)
            .options(
                contains_eager(Atendimento.tecnico).joinedload(Usuario.perfil_tecnico),
            )
            .filter(Atendimento.servico_id == servico_id)
            .order_by(Atendimento.criado_em)
            .all()
        )
