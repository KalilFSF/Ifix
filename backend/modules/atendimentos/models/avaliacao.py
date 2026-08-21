from datetime import datetime, timezone

from database import db
from utils import isoformat_utc


class Avaliacao(db.Model):
    """Avaliação mútua (nota + comentário opcional) entre cliente e técnico
    de um chamado finalizado — cada um avalia o outro uma única vez por
    chamado (uq_avaliacao_servico_autor). Quando o avaliado é o técnico,
    alimenta PerfilTecnico.nota_media (ver AvaliarService), usado pelo
    ranking em SelecionarTecnicosService."""

    __tablename__ = "avaliacoes"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    avaliado_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nota = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("servico_id", "autor_id", name="uq_avaliacao_servico_autor"),
    )

    servico = db.relationship("Servico")
    autor = db.relationship("Usuario", foreign_keys=[autor_id])
    avaliado = db.relationship("Usuario", foreign_keys=[avaliado_id])

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def buscar_por_id(cls, avaliacao_id):
        return cls.query.get(avaliacao_id)

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, servico_id, autor_id, avaliado_id, nota, comentario):
        return cls(
            servico_id=servico_id,
            autor_id=autor_id,
            avaliado_id=avaliado_id,
            nota=nota,
            comentario=comentario or None,
        ).salvar()

    @classmethod
    def buscar_por_servico_e_autor(cls, servico_id, autor_id):
        return cls.query.filter_by(servico_id=servico_id, autor_id=autor_id).first()

    @classmethod
    def listar_por_servico(cls, servico_id):
        return cls.query.filter_by(servico_id=servico_id).order_by(cls.criado_em).all()

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "autor_id": self.autor_id,
            "autor_nome": self.autor.nome if self.autor else None,
            "avaliado_id": self.avaliado_id,
            "avaliado_nome": self.avaliado.nome if self.avaliado else None,
            "nota": self.nota,
            "comentario": self.comentario,
            "criado_em": isoformat_utc(self.criado_em),
        }
