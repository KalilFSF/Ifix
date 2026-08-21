from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

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

    pais = db.Column(db.String(50), nullable=False, default="Brasil")
    cep = db.Column(db.String(9))
    estado = db.Column(db.String(2))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    endereco = db.Column(db.String(150))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(150))

    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
        db.session.commit()
        return self

    def atualizar(self, dados):
        for campo in ("nome", "telefone", "cidade", "estado", "endereco"):
            if campo in dados:
                setattr(self, campo, dados[campo])
        return self.salvar()

    def remover(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, usuario_id):
        return cls.query.get(usuario_id)

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
            role=role,
        )
        usuario.set_senha(senha)
        return usuario.salvar()

    def tornar_tecnico(self):
        self.role = "tecnico"
        return self.salvar()

    # ============== Senha / autenticação ==============

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "cpf": self.cpf,
            "role": self.role,
            "cidade": self.cidade,
            "estado": self.estado,
            "pais": self.pais,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
