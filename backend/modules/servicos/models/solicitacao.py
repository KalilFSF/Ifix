from datetime import datetime, timezone

from constants import (
    SOLICITACAO_ACEITA,
    SOLICITACAO_ORCAMENTO_ENVIADO,
    SOLICITACAO_PENDENTE,
    SOLICITACAO_RECUSADA,
)
from database import db
from utils import isoformat_utc


class SolicitacaoTecnico(db.Model):
    """Chamado oferecido a um técnico específico, aguardando aceite/recusa —
    fica na área "Solicitações pendentes" do painel do técnico, separada
    dos chamados já aceitos (Servico.tecnico_id só é preenchido depois que
    uma dessas é aceita)."""

    __tablename__ = "solicitacoes_tecnicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SOLICITACAO_PENDENTE)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    respondido_em = db.Column(db.DateTime)

    servico = db.relationship("Servico", back_populates="solicitacoes")
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
    def buscar_por_id(cls, solicitacao_id):
        return cls.query.get(solicitacao_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, servico_id, tecnico_id):
        return cls(servico_id=servico_id, tecnico_id=tecnico_id).salvar()

    @classmethod
    def buscar_pendente(cls, servico_id, tecnico_id):
        return cls.query.filter_by(servico_id=servico_id, tecnico_id=tecnico_id, status=SOLICITACAO_PENDENTE).first()

    @classmethod
    def buscar_por_servico_e_tecnico(cls, servico_id, tecnico_id):
        return cls.query.filter_by(servico_id=servico_id, tecnico_id=tecnico_id).first()

    @classmethod
    def listar_pendentes_por_tecnico(cls, tecnico_id):
        return cls.query.filter_by(tecnico_id=tecnico_id, status=SOLICITACAO_PENDENTE).order_by(cls.criado_em.desc()).all()

    @classmethod
    def listar_pendentes_por_servico(cls, servico_id, excluir_id=None):
        query = cls.query.filter(cls.servico_id == servico_id, cls.status == SOLICITACAO_PENDENTE)
        if excluir_id is not None:
            query = query.filter(cls.id != excluir_id)
        return query.all()

    @classmethod
    def listar_abertas_por_servico(cls, servico_id, excluir_tecnico_id=None):
        """Solicitações ainda "vivas" pro chamado (pendente ou já com
        orçamento enviado, mas nenhuma decisão do cliente ainda) — usado
        pra recusar os demais técnicos quando o cliente escolhe um orçamento."""
        query = cls.query.filter(
            cls.servico_id == servico_id,
            cls.status.in_([SOLICITACAO_PENDENTE, SOLICITACAO_ORCAMENTO_ENVIADO]),
        )
        if excluir_tecnico_id is not None:
            query = query.filter(cls.tecnico_id != excluir_tecnico_id)
        return query.all()

    def marcar_aceita(self):
        self.status = SOLICITACAO_ACEITA
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def marcar_recusada(self):
        self.status = SOLICITACAO_RECUSADA
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def marcar_orcamento_enviado(self):
        self.status = SOLICITACAO_ORCAMENTO_ENVIADO
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "tecnico_id": self.tecnico_id,
            "status": self.status,
            "criado_em": isoformat_utc(self.criado_em),
            "respondido_em": isoformat_utc(self.respondido_em),
        }
