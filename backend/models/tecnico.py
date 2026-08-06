from datetime import datetime, timezone

from database import db


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
