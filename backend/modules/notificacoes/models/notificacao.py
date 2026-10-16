from datetime import datetime, timezone

from database import db
from utils import isoformat_utc

# Painel pra onde cada notificação leva, conforme o papel de quem recebe.
LINK_POR_PAPEL = {
    "cliente": "/cliente/chamados",
    "tecnico": "/tecnico/home",
}


class Notificacao(db.Model):
    """Aviso dentro do app (funcionalidade 9) sobre um evento do chamado.

    É o canal que não depende de plataforma externa: o e-mail continua
    existindo, mas quem está com o iFix aberto vê o sino mudar no mesmo
    polling dos painéis. `papel` diz em qual painel o aviso faz sentido —
    a mesma conta pode ser cliente de um chamado e técnico de outro."""

    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"))
    papel = db.Column(db.String(10), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    mensagem = db.Column(db.String(300), nullable=False)

    # Nulo = ainda não vista. Alimenta o contador do sino.
    lida_em = db.Column(db.DateTime)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def buscar_por_id(cls, notificacao_id):
        return cls.query.get(notificacao_id)

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, usuario_id, papel, tipo, titulo, mensagem, servico_id=None):
        return cls(
            usuario_id=usuario_id,
            servico_id=servico_id,
            papel=papel,
            tipo=tipo,
            titulo=titulo[:120],
            mensagem=mensagem[:300],
        ).salvar()

    @classmethod
    def listar_recentes(cls, usuario_id, limite):
        return (
            cls.query.filter_by(usuario_id=usuario_id)
            .order_by(cls.criado_em.desc(), cls.id.desc())
            .limit(limite)
            .all()
        )

    @classmethod
    def contar_nao_lidas(cls, usuario_id):
        return cls.query.filter(cls.usuario_id == usuario_id, cls.lida_em.is_(None)).count()

    @classmethod
    def marcar_todas_lidas(cls, usuario_id):
        atualizadas = cls.query.filter(
            cls.usuario_id == usuario_id, cls.lida_em.is_(None)
        ).update({cls.lida_em: datetime.now(timezone.utc)}, synchronize_session=False)
        db.session.commit()
        return atualizadas

    def marcar_lida(self):
        if self.lida_em is None:
            self.lida_em = datetime.now(timezone.utc)
            self.salvar()
        return self

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "papel": self.papel,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "link": LINK_POR_PAPEL.get(self.papel),
            "lida": self.lida_em is not None,
            "criado_em": isoformat_utc(self.criado_em),
        }
