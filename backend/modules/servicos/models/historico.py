"""Eventos da linha do tempo de um chamado: estado anterior/novo, autor e instante."""
from transactions import persist
from sqlalchemy.dialects.mysql import DATETIME, DOUBLE
from datetime import datetime, timezone

from database import db


class HistoricoServico(db.Model):
    """Log append-only de mudanças de status de um Servico, com data/hora e
    quem alterou — usado pela timeline no painel do técnico e em
    "Acompanhar chamado" do cliente."""

    __tablename__ = "historico_servicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    status_anterior = db.Column(db.String(30))
    status_novo = db.Column(db.String(30), nullable=False)
    # SET NULL (não CASCADE): apagar o usuário que alterou não deve apagar o
    # registro de histórico em si, só perder a referência de quem foi.
    alterado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"))
    alterado_em = db.Column(db.DateTime().with_variant(DATETIME(fsp=6), "mysql"), default=lambda: datetime.now(timezone.utc))

    servico = db.relationship("Servico", back_populates="historico")
    alterado_por = db.relationship("Usuario")

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        persist()
        return self

    def remover(self):
        db.session.delete(self)
        persist()

    @classmethod
    def buscar_por_id(cls, historico_id):
        return db.session.get(cls, historico_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def registrar(cls, servico_id, status_anterior, status_novo, alterado_por_id):
        return cls(
            servico_id=servico_id,
            status_anterior=status_anterior,
            status_novo=status_novo,
            alterado_por_id=alterado_por_id,
        ).salvar()

    @classmethod
    def listar_por_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id).order_by(cls.alterado_em).all()

    def to_dict(self):
        from serialization import to_jsonable
        return to_jsonable(self)
