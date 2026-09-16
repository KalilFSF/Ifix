from datetime import datetime, timedelta, timezone

from constants import CAUSAS_DEFEITO_LABELS, GARANTIA_DIAS, STATUS_FINALIZADO
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

    # Teto de gasto (funcionalidade 6): o quanto o cliente aceita gastar em
    # reparo. Separado de preco_estimado de propósito — preco_estimado é
    # exibido como referência e recebe o acréscimo da garantia (+7%), então
    # não serve de limite. Nulo = cliente não definiu teto.
    valor_maximo_aprovado = db.Column(db.Numeric(10, 2))

    # Gorjeta opcional (valor que o cliente decide somar depois de concluído).
    # Fica separada do preço: não é parte do orçamento, não entra no teto e
    # não é cobrada pelo sistema — a cobrança entra junto com o meio de
    # pagamento, no ponto de extensão marcado em constants.py.
    gorjeta = db.Column(db.Numeric(10, 2))

    garantia = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(30), nullable=False, default="aberto")

    # Raio (km) efetivamente usado na última busca por técnicos. Nulo = só a
    # busca automática da abertura rodou, com RAIO_SELECAO_TECNICOS_KM. É
    # gravado quando o cliente aciona "Ampliar busca", pra cada ampliação
    # partir da anterior em vez de recomeçar do raio padrão.
    raio_busca_km = db.Column(db.Integer)

    # Relatório técnico (funcionalidade 8): preenchido pelo técnico durante o
    # atendimento e exigido antes de finalizar o chamado (ver
    # AtualizarStatusServicoService). causa_defeito é um valor de
    # constants.CAUSAS_DEFEITO — padronizado pra permitir agregação.
    causa_defeito = db.Column(db.String(50))
    laudo_tecnico = db.Column(db.Text)
    solucao_aplicada = db.Column(db.Text)

    # Marco zero da garantia (funcionalidade 2): é a partir daqui que correm
    # os GARANTIA_DIAS. Dá pra derivar do historico_servicos, mas uma coluna
    # explícita evita um JOIN em toda checagem de prazo e deixa a regra
    # legível na própria Model.
    finalizado_em = db.Column(db.DateTime)

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
    aprovacoes = db.relationship(
        "SolicitacaoAprovacao",
        back_populates="servico",
        cascade="all, delete-orphan",
        order_by="SolicitacaoAprovacao.criado_em.desc()",
    )
    # foreign_keys explícito: AcionamentoGarantia aponta pra servicos duas
    # vezes (o chamado com garantia e o chamado novo que ele gera), então o
    # SQLAlchemy não tem como adivinhar qual das duas usar aqui.
    acionamentos_garantia = db.relationship(
        "AcionamentoGarantia",
        foreign_keys="AcionamentoGarantia.servico_id",
        back_populates="servico",
        cascade="all, delete-orphan",
        order_by="AcionamentoGarantia.criado_em.desc()",
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
            valor_maximo_aprovado=dados.get("valor_maximo_aprovado"),
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
        # Marca o início do prazo de garantia na primeira finalização (só na
        # primeira: um chamado reaberto e finalizado de novo não deveria
        # renovar a garantia original sozinho).
        if novo_status == STATUS_FINALIZADO and self.finalizado_em is None:
            self.finalizado_em = datetime.now(timezone.utc)
        return self.salvar()

    def atribuir_tecnico(self, tecnico_id, novo_status):
        self.tecnico_id = tecnico_id
        self.status = novo_status
        return self.salvar()

    def ampliar_raio_busca(self, novo_raio_km):
        self.raio_busca_km = novo_raio_km
        return self.salvar()

    def registrar_gorjeta(self, valor):
        self.gorjeta = valor
        return self.salvar()

    @property
    def tem_gorjeta(self):
        return self.gorjeta is not None

    def registrar_laudo(self, causa_defeito, laudo_tecnico, solucao_aplicada=None):
        self.causa_defeito = causa_defeito
        self.laudo_tecnico = laudo_tecnico
        self.solucao_aplicada = solucao_aplicada
        return self.salvar()

    @property
    def tem_laudo(self):
        return bool(self.causa_defeito and self.laudo_tecnico)

    def elevar_teto(self, valor_adicional):
        """Soma ao teto o valor que o cliente acabou de autorizar. Sem teto
        definido não há o que elevar — o chamado segue sem limite."""
        if self.valor_maximo_aprovado is None:
            return self
        self.valor_maximo_aprovado = float(self.valor_maximo_aprovado) + float(valor_adicional)
        return self.salvar()

    @property
    def tem_teto(self):
        return self.valor_maximo_aprovado is not None

    def cabe_no_teto(self, valor):
        """Sem teto definido, tudo cabe — o cliente optou por não limitar."""
        if not self.tem_teto:
            return True
        return float(valor) <= float(self.valor_maximo_aprovado)

    # ============== Garantia (funcionalidade 2) ==============

    @property
    def garantia_expira_em(self):
        if not self.garantia or self.finalizado_em is None:
            return None
        return self.finalizado_em + timedelta(days=GARANTIA_DIAS)

    @property
    def garantia_ativa(self):
        expira_em = self.garantia_expira_em
        if expira_em is None:
            return False
        # finalizado_em é gravado em UTC, mas o Postgres devolve naive —
        # comparar com utcnow() naive mantém os dois lados na mesma régua.
        return datetime.utcnow() <= self._sem_fuso(expira_em)

    @property
    def garantia_dias_restantes(self):
        expira_em = self.garantia_expira_em
        if expira_em is None:
            return None
        restantes = (self._sem_fuso(expira_em) - datetime.utcnow()).days
        return max(restantes, 0)

    @staticmethod
    def _sem_fuso(momento):
        return momento.replace(tzinfo=None) if momento.tzinfo else momento

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
            "valor_maximo_aprovado": float(self.valor_maximo_aprovado) if self.valor_maximo_aprovado is not None else None,
            "gorjeta": float(self.gorjeta) if self.gorjeta is not None else None,
            "raio_busca_km": self.raio_busca_km,
            "garantia": bool(self.garantia),
            "garantia_ativa": self.garantia_ativa,
            "garantia_expira_em": isoformat_utc(self.garantia_expira_em),
            "garantia_dias_restantes": self.garantia_dias_restantes,
            "finalizado_em": isoformat_utc(self.finalizado_em),
            "status": self.status,
            "causa_defeito": self.causa_defeito,
            "causa_defeito_label": CAUSAS_DEFEITO_LABELS.get(self.causa_defeito),
            "laudo_tecnico": self.laudo_tecnico,
            "solucao_aplicada": self.solucao_aplicada,
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
