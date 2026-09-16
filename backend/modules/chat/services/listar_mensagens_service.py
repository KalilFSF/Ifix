from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.chat.repositories.mensagem_repository import MensagemRepository
from modules.servicos.models.servico import Servico


def garantir_acesso_ao_chat(servico_id, usuario):
    """Regra de acesso compartilhada pelos Services do chat.

    Lê e escreve quem participa do chamado. O chat existe a partir do
    momento em que há um técnico definido (antes disso não há com quem
    conversar) e continua aberto depois de finalizado — é o canal natural
    para tratar a garantia, que só faz sentido depois do fim.
    """
    servico = Servico.buscar_por_id(servico_id)
    if servico is None:
        raise RecursoNaoEncontradoError("Chamado não encontrado.")
    if usuario.id not in (servico.cliente_id, servico.tecnico_id):
        raise PermissaoNegadaError("Acesso negado.")
    return servico


class ListarMensagensService:
    def __init__(self):
        self.mensagem_repository = MensagemRepository()

    def executar(self, servico_id, usuario, desde_id=None):
        garantir_acesso_ao_chat(servico_id, usuario)
        return self.mensagem_repository.listar_por_servico(servico_id, desde_id)


class ContarMensagensNaoLidasService:
    def __init__(self):
        self.mensagem_repository = MensagemRepository()

    def executar(self, usuario):
        return self.mensagem_repository.contar_nao_lidas_por_servico(usuario.id)
