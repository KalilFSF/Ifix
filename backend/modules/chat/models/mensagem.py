from datetime import datetime, timezone

from database import db
from utils import isoformat_utc

MAX_CARACTERES_MENSAGEM = 1000


class MensagemChamado(db.Model):
    """Mensagem trocada entre o cliente e o técnico de um chamado.

    O chat é sempre por chamado, não por par de pessoas: o assunto é o
    aparelho, e as duas partes só têm relação por causa dele. Isso também
    dá o controle de acesso de graça — quem pode ler é quem participa
    daquele Servico (ver ListarMensagensService).
    """

    __tablename__ = "mensagens_chamado"

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False, index=True)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)

    # Nulo = ainda não lida pelo destinatário. É o que alimenta o badge de
    # não lidas nos painéis — sem isso, a única forma de saber que chegou
    # mensagem seria abrir o chamado.
    lida_em = db.Column(db.DateTime)

    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    autor = db.relationship("Usuario", foreign_keys=[autor_id])

    # ============== CRUD (Active Record) ==============

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def buscar_por_id(cls, mensagem_id):
        return cls.query.get(mensagem_id)

    # ============== Finders / operações específicas ==============

    @classmethod
    def criar(cls, servico_id, autor_id, conteudo):
        return cls(servico_id=servico_id, autor_id=autor_id, conteudo=conteudo).salvar()

    @classmethod
    def marcar_lidas(cls, servico_id, destinatario_id):
        """Marca como lidas as mensagens que o destinatário recebeu (ou seja,
        as que NÃO são dele) — chamado quando ele abre o chat."""
        agora = datetime.now(timezone.utc)
        atualizadas = cls.query.filter(
            cls.servico_id == servico_id,
            cls.autor_id != destinatario_id,
            cls.lida_em.is_(None),
        ).update({cls.lida_em: agora}, synchronize_session=False)
        db.session.commit()
        return atualizadas

    def to_dict(self):
        return {
            "id": self.id,
            "servico_id": self.servico_id,
            "autor_id": self.autor_id,
            "autor_nome": self.autor.nome if self.autor else None,
            "conteudo": self.conteudo,
            "lida_em": isoformat_utc(self.lida_em),
            "criado_em": isoformat_utc(self.criado_em),
        }
