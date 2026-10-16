from constants import MAX_NOTIFICACOES_LISTADAS
from modules.notificacoes.models.notificacao import Notificacao


class ListarNotificacoesService:
    """Notificações mais recentes do usuário logado + quantas ainda não foram
    vistas. O total vem de uma contagem própria, e não do tamanho da lista:
    com mais não lidas do que o limite listado, o sino ainda mostra o número certo."""

    def executar(self, usuario):
        return {
            "notificacoes": [
                notificacao.to_dict()
                for notificacao in Notificacao.listar_recentes(usuario.id, MAX_NOTIFICACOES_LISTADAS)
            ],
            "nao_lidas": Notificacao.contar_nao_lidas(usuario.id),
        }
