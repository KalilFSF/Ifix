from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.atendimentos.repositories.atendimento_repository import AtendimentoRepository
from modules.servicos.models.servico import Servico


class ListarOrcamentosService:
    def __init__(self):
        self.atendimento_repository = AtendimentoRepository()

    def executar(self, servico_id, cliente):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode ver os orçamentos.")

        return self.atendimento_repository.listar_por_servico_com_tecnico(servico_id)
