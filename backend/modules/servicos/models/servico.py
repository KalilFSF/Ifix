from datetime import datetime, timezone

from database import db


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    tipo_equipamento = db.Column(db.String(20), nullable=False, default="notebook")
    equipamento = db.Column(db.String(150))
    preco_estimado = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    garantia = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(30), nullable=False, default="aberto")

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id], back_populates="servicos_criados")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], back_populates="servicos_atendidos")
    atendimentos = db.relationship("Atendimento", back_populates="servico", cascade="all, delete-orphan")
    solicitacoes = db.relationship(
        "SolicitacaoTecnico",
        back_populates="servico",
        cascade="all, delete-orphan",
        order_by="SolicitacaoTecnico.criado_em",
    )
    historico = db.relationship(
        "HistoricoServico",
        back_populates="servico",
        cascade="all, delete-orphan",
        order_by="HistoricoServico.alterado_em",
    )
    fotos = db.relationship(
        "FotoServico",
        back_populates="servico",
        cascade="all, delete-orphan",
        order_by="FotoServico.enviado_em",
    )

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def atualizar(self, dados):
        for campo in ("titulo", "descricao", "categoria", "tipo_equipamento", "equipamento", "preco_estimado", "garantia"):
            if campo in dados:
                setattr(self, campo, dados[campo])
        return self.salvar()

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, servico_id):
        return cls.query.get(servico_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.order_by(cls.criado_em.desc()).all()

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, dados, cliente_id):
        servico = cls(
            titulo=dados["titulo"],
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            tipo_equipamento=dados["tipo_equipamento"],
            equipamento=dados.get("equipamento"),
            preco_estimado=dados.get("preco_estimado", 0),
            garantia=bool(dados.get("garantia", False)),
            cliente_id=cliente_id,
            status="aberto",
        )
        return servico.salvar()

    @classmethod
    def listar_por_status(cls, status=None):
        query = cls.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.criado_em.desc()).all()

    def atualizar_status(self, novo_status):
        self.status = novo_status
        return self.salvar()

    def atribuir_tecnico(self, tecnico_id, novo_status):
        self.tecnico_id = tecnico_id
        self.status = novo_status
        return self.salvar()

    @property
    def codigo(self):
        return f"IFX-{1000 + self.id}"

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "tipo_equipamento": self.tipo_equipamento,
            "equipamento": self.equipamento,
            "preco_estimado": float(self.preco_estimado) if self.preco_estimado is not None else 0.0,
            "garantia": bool(self.garantia),
            "status": self.status,
            "cliente_id": self.cliente_id,
            "tecnico_id": self.tecnico_id,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "fotos": [foto.to_dict() for foto in self.fotos],
        }

    def to_dict_painel(self):
        """Versão enriquecida usada pelo painel do técnico e por "Acompanhar
        chamado" do cliente — inclui os dados do cliente/técnico."""
        dados = self.to_dict()
        dados["cliente"] = (
            {"id": self.cliente.id, "nome": self.cliente.nome, "telefone": self.cliente.telefone}
            if self.cliente else None
        )
        dados["tecnico"] = (
            {"id": self.tecnico.id, "nome": self.tecnico.nome, "telefone": self.tecnico.telefone}
            if self.tecnico else None
        )
        return dados


class FotoServico(db.Model):
    """Referência a uma foto anexada a um chamado — o arquivo fica em
    frontend/uploads/chamados/; o banco guarda só o nome do arquivo."""

    __tablename__ = "fotos_servicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    arquivo = db.Column(db.String(255), nullable=False)
    enviado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    servico = db.relationship("Servico", back_populates="fotos")

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def criar(cls, servico_id, nome_arquivo):
        return cls(servico_id=servico_id, arquivo=nome_arquivo).salvar()

    def to_dict(self):
        return {
            "id": self.id,
            "arquivo": self.arquivo,
            "url": f"/uploads/chamados/{self.arquivo}",
            "enviado_em": self.enviado_em.isoformat() if self.enviado_em else None,
        }
