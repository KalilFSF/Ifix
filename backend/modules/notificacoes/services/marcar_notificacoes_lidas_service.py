from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.notificacoes.models.notificacao import Notificacao


class MarcarNotificacoesLidasService:
    """Marca como vistas todas as notificações do usuário, ou só uma."""

    def executar_todas(self, usuario):
        return Notificacao.marcar_todas_lidas(usuario.id)

    def executar_uma(self, notificacao_id, usuario):
        notificacao = Notificacao.buscar_por_id(notificacao_id)
        if notificacao is None:
            raise RecursoNaoEncontradoError("Notificação não encontrada.")
        if notificacao.usuario_id != usuario.id:
            raise PermissaoNegadaError("Acesso negado.")
        return notificacao.marcar_lida()
