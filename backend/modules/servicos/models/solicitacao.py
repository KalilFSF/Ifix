from datetime import datetime, timezone

from database import db


class SolicitacaoTecnico(db.Model):
    """Chamado oferecido a um técnico específico, aguardando aceite/recusa —
    fica na área "Solicitações pendentes" do painel do técnico, separada
    dos chamados já aceitos (Servico.tecnico_id só é preenchido depois que
    uma dessas é aceita)."""

    __tablename__ = "solicitacoes_tecnicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pendente")
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
        return cls.query.filter_by(servico_id=servico_id, tecnico_id=tecnico_id, status="pendente").first()

    @classmethod
    def listar_pendentes_por_tecnico(cls, tecnico_id):
        return cls.query.filter_by(tecnico_id=tecnico_id, status="pendente").order_by(cls.criado_em.desc()).all()

    @classmethod
    def listar_pendentes_por_servico(cls, servico_id, excluir_id=None):
        query = cls.query.filter(cls.servico_id == servico_id, cls.status == "pendente")
        if excluir_id is not None:
            query = query.filter(cls.id != excluir_id)
        return query.all()

    def marcar_aceita(self):
        self.status = "aceita"
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def marcar_recusada(self):
        self.status = "recusada"
        self.respondido_em = datetime.now(timezone.utc)
        return self.salvar()

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "tecnico_id": self.tecnico_id,
            "status": self.status,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "respondido_em": self.respondido_em.isoformat() if self.respondido_em else None,
        }

    def to_dict_painel(self):
        """Versão enriquecida usada pela área "Solicitações pendentes" do
        painel do técnico — servico/cliente já vêm carregados pelo JOIN do
        SolicitacaoRepository, então acessar self.servico.cliente aqui não
        dispara consulta nova."""
        dados = self.to_dict()
        dados["servico"] = self.servico.to_dict() if self.servico else None
        dados["cliente"] = (
            {"id": self.servico.cliente.id, "nome": self.servico.cliente.nome, "telefone": self.servico.cliente.telefone}
            if self.servico and self.servico.cliente else None
        )
        return dados
