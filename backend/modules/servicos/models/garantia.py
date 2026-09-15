from datetime import datetime, timezone

from constants import (
    GARANTIA_STATUS_APROVADO,
    GARANTIA_STATUS_CONCLUIDO,
    GARANTIA_STATUS_PENDENTE,
    GARANTIA_STATUS_RECUSADO,
    GARANTIA_TIPOS_LABELS,
)
from database import db
from utils import isoformat_utc


class AcionamentoGarantia(db.Model):
    """Acionamento da garantia contratada (funcionalidade 2).

    O cliente que pagou os +7% tem GARANTIA_DIAS após a finalização pra
    dizer que o problema voltou, e escolhe entre reembolso ou um novo
    atendimento gratuito. No caso de novo atendimento, um chamado novo é
    aberto já atribuído ao mesmo técnico e com preço zero — servico_novo_id
    guarda essa ligação, pra dar pra navegar do acionamento até o reparo que
    ele gerou."""

    __tablename__ = "acionamentos_garantia"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao_problema = db.Column(db.Text, nullable=False)
    tipo_solicitado = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=GARANTIA_STATUS_PENDENTE)
    # SET NULL: apagar o chamado gerado não deve apagar o registro de que a
    # garantia foi acionada — só perder a referência.
    servico_novo_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="SET NULL"))
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    respondido_em = db.Column(db.DateTime)

    servico = db.relationship("Servico", foreign_keys=[servico_id], back_populates="acionamentos_garantia")
    servico_novo = db.relationship("Servico", foreign_keys=[servico_novo_id])
    cliente = db.relationship("Usuario")

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, acionamento_id):
        return cls.query.get(acionamento_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.order_by(cls.criado_em.desc()).all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, servico_id, cliente_id, descricao_problema, tipo_solicitado):
        return cls(
            servico_id=servico_id,
            cliente_id=cliente_id,
            descricao_problema=descricao_problema,
            tipo_solicitado=tipo_solicitado,
            status=GARANTIA_STATUS_PENDENTE,
        ).salvar()

    @classmethod
    def buscar_em_andamento_do_servico(cls, servico_id):
        """Acionamento que ainda não se encerrou. "Aprovado" conta como em
        andamento: o novo atendimento já foi aberto e ainda está rodando —
        só "concluído" e "recusado" liberam um acionamento novo."""
        return cls.query.filter(
            cls.servico_id == servico_id,
            cls.status.in_((GARANTIA_STATUS_PENDENTE, GARANTIA_STATUS_APROVADO)),
        ).first()

    @classmethod
    def listar_por_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id).order_by(cls.criado_em.desc()).all()

    def vincular_servico_novo(self, servico_novo_id):
        self.servico_novo_id = servico_novo_id
        self.status = GARANTIA_STATUS_APROVADO
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def marcar_concluido(self):
        self.status = GARANTIA_STATUS_CONCLUIDO
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def recusar(self):
        self.status = GARANTIA_STATUS_RECUSADO
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "cliente_id": self.cliente_id,
            "descricao_problema": self.descricao_problema,
            "tipo_solicitado": self.tipo_solicitado,
            "tipo_solicitado_label": GARANTIA_TIPOS_LABELS.get(self.tipo_solicitado),
            "status": self.status,
            "servico_novo_id": self.servico_novo_id,
            "servico_novo_codigo": self.servico_novo.codigo if self.servico_novo else None,
            "criado_em": isoformat_utc(self.criado_em),
            "respondido_em": isoformat_utc(self.respondido_em),
        }
