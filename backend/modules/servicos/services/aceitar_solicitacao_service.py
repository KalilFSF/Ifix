from constants import STATUS_AGUARDANDO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class AceitarSolicitacaoService:
    def executar(self, solicitacao_id, tecnico_id):
        solicitacao = SolicitacaoTecnico.buscar_por_id(solicitacao_id)
        if solicitacao is None:
            raise RecursoNaoEncontradoError("Solicitação não encontrada.")
        if solicitacao.tecnico_id != tecnico_id:
            raise PermissaoNegadaError("Esta solicitação não pertence a este técnico.")
        if solicitacao.status != "pendente":
            raise SolicitacaoJaRespondidaError("Esta solicitação já foi respondida.")

        solicitacao.marcar_aceita()

        servico = solicitacao.servico
        status_anterior = servico.status
        servico.atribuir_tecnico(tecnico_id, STATUS_AGUARDANDO)
        HistoricoServico.registrar(servico.id, status_anterior, STATUS_AGUARDANDO, tecnico_id)

        for outra in SolicitacaoTecnico.listar_pendentes_por_servico(servico.id, excluir_id=solicitacao.id):
            outra.marcar_recusada()

        return solicitacao
