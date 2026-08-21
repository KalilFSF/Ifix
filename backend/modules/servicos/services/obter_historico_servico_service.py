from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico


class ObterHistoricoServicoService:
    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if usuario.id not in {servico.cliente_id, servico.tecnico_id}:
            raise PermissaoNegadaError("Acesso negado.")

        return HistoricoServico.listar_por_servico(servico_id)
