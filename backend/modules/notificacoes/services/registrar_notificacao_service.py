"""Persiste o aviso interno como parte da transação de negócio que o originou."""
from transactions import atomic
from modules.notificacoes.models.notificacao import Notificacao

class RegistrarNotificacaoService:
    @staticmethod
    @atomic
    def executar(usuario_id,papel,tipo,titulo,mensagem,servico_id=None):
        if usuario_id is None:
            return None
        return Notificacao.criar(usuario_id,papel,tipo,titulo,mensagem,servico_id)
