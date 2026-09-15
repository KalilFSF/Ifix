from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.servicos.models.servico import Servico
from modules.servicos.repositories.aprovacao_repository import AprovacaoRepository


class ListarAprovacoesService:
    """Autorizações de custo adicional de um chamado, para os dois lados: o
    cliente vê o que precisa responder, o técnico acompanha o que pediu."""

    def __init__(self):
        self.aprovacao_repository = AprovacaoRepository()

    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if usuario.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        return self.aprovacao_repository.listar_por_servico(servico_id)
