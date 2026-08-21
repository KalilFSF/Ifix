from constants import STATUS_ABERTO, STATUS_AGUARDANDO, STATUS_CANCELADO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico


class CancelarServicoService:
    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != usuario.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode cancelar este chamado.")

        if servico.status not in {STATUS_ABERTO, STATUS_AGUARDANDO}:
            raise ValidacaoError("Só é possível cancelar chamados ainda abertos ou aguardando atendimento.")

        status_anterior = servico.status
        servico.status = STATUS_CANCELADO
        servico.salvar()
        HistoricoServico.registrar(servico.id, status_anterior, STATUS_CANCELADO, usuario.id)
        return servico


class ExcluirServicoService:
    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != usuario.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode excluir este chamado.")

        if servico.status not in {STATUS_ABERTO, STATUS_AGUARDANDO, STATUS_CANCELADO}:
            raise ValidacaoError("Só é possível excluir chamados ainda abertos, aguardando ou cancelados.")

        servico.remover()
        return True
