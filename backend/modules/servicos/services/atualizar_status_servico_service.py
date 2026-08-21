from constants import STATUS_TECNICO_CHOICES
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico


class AtualizarStatusServicoService:
    def executar(self, servico_id, novo_status, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if novo_status not in STATUS_TECNICO_CHOICES:
            raise ValidacaoError(f"Status inválido: {novo_status}")
        if servico.tecnico_id != usuario.id:
            raise PermissaoNegadaError("Apenas o técnico responsável pode atualizar este chamado.")

        status_anterior = servico.status
        servico.atualizar_status(novo_status)
        HistoricoServico.registrar(servico.id, status_anterior, novo_status, usuario.id)
        return servico
