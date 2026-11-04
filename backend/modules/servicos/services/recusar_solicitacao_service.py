"""Valida o técnico dono do convite antes de registrar a recusa."""
from transactions import atomic, lock_model, lock_child
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class RecusarSolicitacaoService:
    @atomic
    def executar(self, solicitacao_id, tecnico_id):
        solicitacao = lock_child(SolicitacaoTecnico, solicitacao_id)
        if solicitacao is None:
            raise RecursoNaoEncontradoError("Solicitação não encontrada.")
        if solicitacao.tecnico_id != tecnico_id:
            raise PermissaoNegadaError("Esta solicitação não pertence a este técnico.")
        if solicitacao.status != "pendente":
            raise SolicitacaoJaRespondidaError("Esta solicitação já foi respondida.")

        return solicitacao.marcar_recusada()
