from datetime import datetime, timezone

from database import db
from utils import isoformat_utc


class HistoricoServico(db.Model):
    """Log append-only de mudanças de status de um Servico, com data/hora e
    quem alterou — usado pela timeline no painel do técnico e em
    "Acompanhar chamado" do cliente."""

    __tablename__ = "historico_servicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    status_anterior = db.Column(db.String(30))
    status_novo = db.Column(db.String(30), nullable=False)
    alterado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    alterado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    servico = db.relationship("Servico", back_populates="historico")
    alterado_por = db.relationship("Usuario")

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, historico_id):
        return cls.query.get(historico_id)

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
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "status_anterior": self.status_anterior,
            "status_novo": self.status_novo,
            "alterado_por_id": self.alterado_por_id,
            "alterado_por_nome": self.alterado_por.nome if self.alterado_por else None,
            "alterado_em": isoformat_utc(self.alterado_em),
        }
