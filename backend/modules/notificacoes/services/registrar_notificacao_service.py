from database import db
from modules.notificacoes.models.notificacao import Notificacao


class RegistrarNotificacaoService:
    """Cria a notificação no app de um evento do chamado (funcionalidade 9).

    Best-effort, como o EmailService: o aviso nunca pode derrubar a ação que
    o gerou — quando este Service roda, a ação principal já foi gravada, e
    devolver 500 por causa do sino faria o usuário repetir algo que deu certo."""

    @staticmethod
    def executar(usuario_id, papel, tipo, titulo, mensagem, servico_id=None):
        if usuario_id is None:
            return None
        try:
            return Notificacao.criar(usuario_id, papel, tipo, titulo, mensagem, servico_id)
        except Exception as erro:  # noqa: BLE001 — falha de aviso não é falha da ação
            db.session.rollback()
            print(f"[notificacao] não foi possível registrar o aviso: {erro}")
            return None
