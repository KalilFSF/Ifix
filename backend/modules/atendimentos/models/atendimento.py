from datetime import datetime, timezone

from database import db
from utils import isoformat_utc


class Atendimento(db.Model):
    __tablename__ = "atendimentos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pendente")
    valor_orcamento = db.Column(db.Numeric(10, 2), nullable=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id], back_populates="atendimentos_cliente")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], back_populates="atendimentos_tecnico")
    servico = db.relationship("Servico", back_populates="atendimentos")

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def atualizar(self, dados):
        for campo in ("titulo", "descricao", "status", "valor_orcamento"):
            if campo in dados:
                setattr(self, campo, dados[campo])
        return self.salvar()

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, atendimento_id):
        return cls.query.get(atendimento_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, dados, servico_id, usuario_id, role):
        atendimento = cls(
            titulo=dados.get("titulo") or "Orçamento",
            descricao=dados.get("descricao") or "Orçamento enviado para o cliente.",
            status=dados.get("status", "pendente"),
            valor_orcamento=dados.get("valor_orcamento"),
            cliente_id=dados.get("cliente_id"),
            servico_id=servico_id,
        )
        # cliente_id é NOT NULL: quem cria precisa já estar identificado
        # (como cliente ou como técnico) antes do primeiro salvar().
        if role == "cliente":
            atendimento.cliente_id = usuario_id
        else:
            atendimento.tecnico_id = usuario_id
        return atendimento.salvar()

    @classmethod
    def buscar_por_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id).first()

    @classmethod
    def listar_por_usuario(cls, usuario_id, role):
        if role == "tecnico":
            return cls.query.filter_by(tecnico_id=usuario_id).order_by(cls.criado_em.desc()).all()
        if role == "cliente":
            return cls.query.filter_by(cliente_id=usuario_id).order_by(cls.criado_em.desc()).all()
        return []

    def definir_responsavel(self, usuario_id, role):
        if role == "cliente":
            self.cliente_id = usuario_id
        else:
            self.tecnico_id = usuario_id
        return self.salvar()

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
            "criado_em": isoformat_utc(self.criado_em),
            "atualizado_em": isoformat_utc(self.atualizado_em),
        }
