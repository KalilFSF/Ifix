"""Conta, identidade, senha em hash e dados pessoais; pode exercer papel de cliente ou técnico."""
from transactions import persist
from sqlalchemy.dialects.mysql import DATETIME, DOUBLE
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from constants import (
    HORARIO_ATENDIMENTO_PADRAO_FIM,
    HORARIO_ATENDIMENTO_PADRAO_INICIO,
    LIMITE_ALERTAS_COMPORTAMENTO,
)
from database import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Foto de perfil (URL do Cloudinary). Fica em Usuario, e não só em
    # PerfilTecnico, porque ter rosto na conta não é atributo de técnico:
    # o cliente também aparece pro técnico no painel dele. Para técnicos
    # antigos o valor pode estar nulo aqui e preenchido em
    # PerfilTecnico.foto_perfil — to_dict() resolve com fallback.
    foto_perfil = db.Column(db.String(255))

    pais = db.Column(db.String(50), nullable=False, default="Brasil")
    cep = db.Column(db.String(9))
    estado = db.Column(db.String(2))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    endereco = db.Column(db.String(150))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(150))

    # Coordenadas do endereço cadastrado — usadas pelo ranking de técnicos
    # (distância via Haversine, ver SelecionarTecnicosService). Para o
    # técnico é a localização usada no cálculo; para o cliente, servem de
    # padrão para Servico.latitude/longitude no momento da criação do chamado.
    latitude = db.Column(db.Float().with_variant(DOUBLE(), "mysql"))
    longitude = db.Column(db.Float().with_variant(DOUBLE(), "mysql"))

    # Penalidade por comportamento (funcionalidade 4): incrementado sempre
    # que um técnico avalia essa conta com nota baixa de comportamento/
    # colaboração num chamado (ver AvaliarService); ao atingir o limite,
    # a conta é suspensa automaticamente e não pode mais abrir chamados
    # novos (ver CriarServicoService).
    alertas_comportamento = db.Column(db.Integer, nullable=False, default=0)
    suspenso = db.Column(db.Boolean, nullable=False, default=False)

    # Restrição de horário (funcionalidade 9): faixa "HH:MM" em que o usuário
    # aceita ser atendido/acionado. Cliente usa pra não receber contato fora
    # de hora; técnico, pra não ser notificado de chamado fora do expediente
    # (ver SolicitarTecnicosService).
    horario_inicio_atendimento = db.Column(
        db.String(5), nullable=False, default=HORARIO_ATENDIMENTO_PADRAO_INICIO
    )
    horario_fim_atendimento = db.Column(
        db.String(5), nullable=False, default=HORARIO_ATENDIMENTO_PADRAO_FIM
    )

    # NULL em contas antigas: não atribuir retroativamente um aceite inexistente.
    termos_versao = db.Column(db.String(32))
    privacidade_versao = db.Column(db.String(32))
    termos_aceitos_em = db.Column(db.DateTime().with_variant(DATETIME(fsp=6), "mysql"))

    criado_em = db.Column(db.DateTime().with_variant(DATETIME(fsp=6), "mysql"), default=lambda: datetime.now(timezone.utc))

    perfil_tecnico = db.relationship(
        "PerfilTecnico",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    servicos_criados = db.relationship(
        "Servico",
        foreign_keys="Servico.cliente_id",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )
    servicos_atendidos = db.relationship(
        "Servico",
        foreign_keys="Servico.tecnico_id",
        back_populates="tecnico",
        cascade="all, delete-orphan",
    )
    atendimentos_cliente = db.relationship(
        "Atendimento",
        foreign_keys="Atendimento.cliente_id",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )
    atendimentos_tecnico = db.relationship(
        "Atendimento",
        foreign_keys="Atendimento.tecnico_id",
        back_populates="tecnico",
        cascade="all, delete-orphan",
    )

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        persist()
        return self

    # cep/bairro/numero/complemento entraram na lista: eles existem como
    # coluna desde sempre, mas PATCH /api/me os descartava em silêncio —
    # quem mandasse um CEP novo recebia 200 e nada mudava.
    CAMPOS_EDITAVEIS = (
        "nome", "telefone", "cep", "estado", "cidade", "bairro",
        "endereco", "numero", "complemento", "foto_perfil",
        "latitude", "longitude",
    )

    def atualizar(self, dados):
        for campo in self.CAMPOS_EDITAVEIS:
            if campo in dados:
                setattr(self, campo, dados[campo])
        return self.salvar()

    def definir_foto_perfil(self, url):
        self.foto_perfil = url
        return self.salvar()

    def remover(self):
        db.session.delete(self)
        persist()

    def registrar_alerta_comportamento(self):
        """Chamado quando um técnico avalia essa conta com nota baixa de
        comportamento/colaboração — ao acumular LIMITE_ALERTAS_COMPORTAMENTO
        alertas, suspende a conta automaticamente (não pode mais abrir
        chamados novos, ver CriarServicoService)."""
        self.alertas_comportamento = (self.alertas_comportamento or 0) + 1
        if self.alertas_comportamento >= LIMITE_ALERTAS_COMPORTAMENTO:
            self.suspenso = True
        return self.salvar()

    def definir_horario_atendimento(self, inicio, fim):
        self.horario_inicio_atendimento = inicio
        self.horario_fim_atendimento = fim
        return self.salvar()

    @classmethod
    def buscar_por_id(cls, usuario_id):
        return db.session.get(cls, usuario_id)

    @classmethod
    def listar_todos(cls):
        return cls.query.all()

    # ============== Finders específicos ==============

    @classmethod
    def buscar_por_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def buscar_por_cpf(cls, cpf):
        return cls.query.filter_by(cpf=cpf).first()

    @classmethod
    def listar_por_role(cls, role):
        return cls.query.filter_by(role=role).all()

    @classmethod
    def criar(cls, dados, senha, role):
        from legal import validar_aceite, TERMOS_VERSAO, PRIVACIDADE_VERSAO
        validar_aceite(dados)
        usuario = cls(
            nome=dados["nome"],
            email=dados["email"],
            telefone=dados["telefone"],
            cpf=dados["cpf"],
            data_nascimento=dados["data_nascimento"],
            pais=dados["pais"],
            cep=dados["cep"] or None,
            estado=dados["estado"] or None,
            cidade=dados["cidade"] or None,
            bairro=dados["bairro"] or None,
            endereco=dados["endereco"] or None,
            numero=dados["numero"] or None,
            complemento=dados["complemento"] or None,
            latitude=dados.get("latitude"),
            longitude=dados.get("longitude"),
            role=role,
            termos_versao=TERMOS_VERSAO,
            privacidade_versao=PRIVACIDADE_VERSAO,
            termos_aceitos_em=datetime.now(timezone.utc),
        )
        usuario.set_senha(senha)
        return usuario.salvar()

    def tornar_tecnico(self):
        self.role = "tecnico"
        return self.salvar()

    @property
    def eh_tecnico(self):
        """True se a conta tem capacidade de técnico (perfil anexado ou role).
        Ser técnico NÃO impede usar a área de cliente."""
        return self.role == "tecnico" or self.perfil_tecnico is not None

    # ============== Senha / autenticação ==============

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        from serialization import to_jsonable
        return to_jsonable(self)
