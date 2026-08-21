from exceptions import RecursoNaoEncontradoError
from modules.servicos.models.servico import Servico


class ObterDetalhesServicoService:
    def executar(self, servico_id):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        return servico
