from datetime import datetime, timezone

from database import db
from utils import isoformat_utc


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

    # Localização do chamado, usada por SelecionarTecnicosService pra
    # calcular distância (Haversine) até cada técnico. Preenchida em
    # Servico.criar a partir do endereço do cliente (Usuario.latitude/
    # longitude); pode ficar nula se o cliente ainda não tem lat/long
    # cadastrados, caso em que a seleção automática é pulada.
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"))
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
            latitude=dados.get("latitude"),
            longitude=dados.get("longitude"),
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
            "latitude": self.latitude,
            "longitude": self.longitude,
            "cliente_id": self.cliente_id,
            "tecnico_id": self.tecnico_id,
            "criado_em": isoformat_utc(self.criado_em),
            "atualizado_em": isoformat_utc(self.atualizado_em),
            "fotos": [foto.to_dict() for foto in self.fotos],
        }


class FotoServico(db.Model):
    """Referência a uma foto anexada a um chamado — o upload vai pro
    Cloudinary (ver utils.salvar_arquivo) e o banco guarda a URL pública
    completa retornada por ele, não um nome de arquivo local."""

    __tablename__ = "fotos_servicos"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
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
            "url": self.arquivo,
            "enviado_em": isoformat_utc(self.enviado_em),
        }
