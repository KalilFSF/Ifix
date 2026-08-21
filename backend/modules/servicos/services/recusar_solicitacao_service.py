from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class RecusarSolicitacaoService:
    def executar(self, solicitacao_id, tecnico_id):
        solicitacao = SolicitacaoTecnico.buscar_por_id(solicitacao_id)
        if solicitacao is None:
            raise RecursoNaoEncontradoError("Solicitação não encontrada.")
        if solicitacao.tecnico_id != tecnico_id:
            raise PermissaoNegadaError("Esta solicitação não pertence a este técnico.")
        if solicitacao.status != "pendente":
            raise SolicitacaoJaRespondidaError("Esta solicitação já foi respondida.")

        return solicitacao.marcar_recusada()
