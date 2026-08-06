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
