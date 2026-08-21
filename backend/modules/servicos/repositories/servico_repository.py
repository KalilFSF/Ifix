from sqlalchemy.orm import aliased, contains_eager

from database import db
from modules.servicos.models.servico import Servico
from modules.usuarios.models.usuario import Usuario


class ServicoRepository:
    """Consultas de Servico que extrapolam CRUD simples (JOIN com os
    participantes) — usado pelo painel do técnico e por "Acompanhar
    chamado" do cliente, que precisam do nome/telefone de cliente e
    técnico junto com cada chamado, sem N+1 query por linha."""

    def buscar_meus_com_participantes(self, usuario_id, role, status=None):
        # Servico se relaciona com Usuario duas vezes (cliente e técnico) —
        # precisa de alias explícito, senão o SQL gera "usuarios" duas
        # vezes na mesma query e o banco não sabe distinguir as colunas.
        cliente_usuario = aliased(Usuario)
        tecnico_usuario = aliased(Usuario)

        query = (
            db.session.query(Servico)
            .join(cliente_usuario, Servico.cliente_id == cliente_usuario.id)
            .outerjoin(tecnico_usuario, Servico.tecnico_id == tecnico_usuario.id)
            .options(
                contains_eager(Servico.cliente.of_type(cliente_usuario)),
                contains_eager(Servico.tecnico.of_type(tecnico_usuario)),
            )
        )

        if role == "tecnico":
            query = query.filter(Servico.tecnico_id == usuario_id)
        elif role == "cliente":
            query = query.filter(Servico.cliente_id == usuario_id)
        else:
            return []

        if status:
            query = query.filter(Servico.status == status)

        return query.order_by(Servico.criado_em.desc()).all()
