from datetime import datetime, timezone

from database import db


class Atendimento(db.Model):
    __tablename__ = "atendimentos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pendente")
    valor_orcamento = db.Column(db.Numeric(10, 2), nullable=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id], back_populates="atendimentos_cliente")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], back_populates="atendimentos_tecnico")
    servico = db.relationship("Servico", back_populates="atendimentos")

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "status": self.status,
            "valor_orcamento": float(self.valor_orcamento) if self.valor_orcamento is not None else None,
            "cliente_id": self.cliente_id,
            "tecnico_id": self.tecnico_id,
            "servico_id": self.servico_id,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
