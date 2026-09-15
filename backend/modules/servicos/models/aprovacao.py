from datetime import datetime, timezone

from constants import APROVACAO_APROVADA, APROVACAO_PENDENTE, APROVACAO_RECUSADA
from database import db
from utils import isoformat_utc


class SolicitacaoAprovacao(db.Model):
    """Pedido de autorização de custo adicional (funcionalidades 6 e 7).

    Quando o técnico encontra um problema novo durante o reparo, ele não
    executa nada por conta própria: descreve o que achou, informa quanto
    custa a mais e espera o cliente autorizar remotamente. É o mecanismo que
    faz o teto de gasto (Servico.valor_maximo_aprovado) valer de verdade —
    sem ele, o limite seria só um número informativo."""

    __tablename__ = "solicitacoes_aprovacao"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    valor_adicional = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=APROVACAO_PENDENTE)
    justificativa_recusa = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    respondido_em = db.Column(db.DateTime)

    servico = db.relationship("Servico", back_populates="aprovacoes")
    tecnico = db.relationship("Usuario")

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, aprovacao_id):
        return cls.query.get(aprovacao_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.order_by(cls.criado_em.desc()).all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, servico_id, tecnico_id, descricao, valor_adicional):
        return cls(
            servico_id=servico_id,
            tecnico_id=tecnico_id,
            descricao=descricao,
            valor_adicional=valor_adicional,
            status=APROVACAO_PENDENTE,
        ).salvar()

    @classmethod
    def buscar_pendente_do_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id, status=APROVACAO_PENDENTE).first()

    @classmethod
    def listar_por_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id).order_by(cls.criado_em.desc()).all()

    @classmethod
    def somar_aprovadas(cls, servico_id):
        """Total já autorizado a mais neste chamado — é o que o teto do
        cliente absorveu além do orçamento original."""
        total = (
            db.session.query(db.func.coalesce(db.func.sum(cls.valor_adicional), 0))
            .filter_by(servico_id=servico_id, status=APROVACAO_APROVADA)
            .scalar()
        )
        return float(total or 0)

    def aprovar(self):
        self.status = APROVACAO_APROVADA
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def recusar(self, justificativa=None):
        self.status = APROVACAO_RECUSADA
        self.justificativa_recusa = justificativa
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    @property
    def pendente(self):
        return self.status == APROVACAO_PENDENTE

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "tecnico_id": self.tecnico_id,
            "tecnico_nome": self.tecnico.nome if self.tecnico else None,
            "descricao": self.descricao,
            "valor_adicional": float(self.valor_adicional) if self.valor_adicional is not None else 0.0,
            "status": self.status,
            "justificativa_recusa": self.justificativa_recusa,
            "criado_em": isoformat_utc(self.criado_em),
            "respondido_em": isoformat_utc(self.respondido_em),
        }
