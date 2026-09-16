from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.atendimentos.repositories.avaliacao_repository import AvaliacaoRepository
from modules.servicos.models.servico import Servico


class ListarAvaliacoesService:
    def __init__(self):
        self.avaliacao_repository = AvaliacaoRepository()

    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if usuario.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        return self.avaliacao_repository.listar_por_servico(servico_id)
