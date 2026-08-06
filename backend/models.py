# Tabelas do banco (SQLAlchemy) para o sistema IFix.

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


class PerfilTecnico(db.Model):
    __tablename__ = "perfis_tecnicos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)

    especialidade = db.Column(db.String(100), nullable=False)
    escolaridade = db.Column(db.String(50), nullable=False)
    curso_superior = db.Column(db.String(100))
    regiao_atendimento = db.Column(db.String(150), nullable=False)
    cursos_experiencias = db.Column(db.Text)
    especializacoes = db.Column(db.Text)
    foto_perfil = db.Column(db.String(255), nullable=False)

    usuario = db.relationship("Usuario", back_populates="perfil_tecnico")
    diplomas = db.relationship(
        "Diploma",
        back_populates="perfil_tecnico",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "especialidade": self.especialidade,
            "escolaridade": self.escolaridade,
            "curso_superior": self.curso_superior,
            "regiao_atendimento": self.regiao_atendimento,
            "cursos_experiencias": self.cursos_experiencias,
            "especializacoes": self.especializacoes,
            "foto_perfil": self.foto_perfil,
        }


class Diploma(db.Model):
    __tablename__ = "diplomas"

    id = db.Column(db.Integer, primary_key=True)
    perfil_tecnico_id = db.Column(db.Integer, db.ForeignKey("perfis_tecnicos.id"), nullable=False)
    arquivo = db.Column(db.String(255), nullable=False)
    enviado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    perfil_tecnico = db.relationship("PerfilTecnico", back_populates="diplomas")

    def to_dict(self):
        return {"id": self.id, "arquivo": self.arquivo, "enviado_em": self.enviado_em.isoformat() if self.enviado_em else None}


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    preco_estimado = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="aberto")

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id], back_populates="servicos_criados")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], back_populates="servicos_atendidos")
    atendimentos = db.relationship("Atendimento", back_populates="servico", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "preco_estimado": float(self.preco_estimado) if self.preco_estimado is not None else 0.0,
            "status": self.status,
            "cliente_id": self.cliente_id,
            "tecnico_id": self.tecnico_id,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }


class Atendimento(db.Model):
    __tablename__ = "atendimentos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pendente")
    valor_orcamento = db.Column(db.Numeric(10, 2), nullable=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Usuario", foreign_keys=[cliente_id], back_populates="atendimentos_cliente")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], back_populates="atendimentos_tecnico")
    servico = db.relationship("Servico", back_populates="atendimentos")

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
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
