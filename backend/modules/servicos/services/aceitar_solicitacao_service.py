"""Preserva o aceite direto legado, exigindo convite válido e chamado ainda não decidido."""
from transactions import atomic, lock_model, lock_child
from constants import NOTIFICACAO_TECNICO_DEFINIDO, STATUS_AGUARDANDO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError, ValidacaoError
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class AceitarSolicitacaoService:
    @atomic
    def executar(self, solicitacao_id, tecnico_id):
        solicitacao = lock_child(SolicitacaoTecnico, solicitacao_id)
        if solicitacao is None:
            raise RecursoNaoEncontradoError("Solicitação não encontrada.")
        if solicitacao.tecnico_id != tecnico_id:
            raise PermissaoNegadaError("Esta solicitação não pertence a este técnico.")
        if solicitacao.status != "pendente":
            raise SolicitacaoJaRespondidaError("Esta solicitação já foi respondida.")

        if solicitacao.servico.status != "aberto" or solicitacao.servico.tecnico_id is not None:
            raise ValidacaoError("Este chamado já foi decidido ou encerrado.")
        solicitacao.marcar_aceita()

        servico = solicitacao.servico
        status_anterior = servico.status
        servico.atribuir_tecnico(tecnico_id, STATUS_AGUARDANDO)
        HistoricoServico.registrar(servico.id, status_anterior, STATUS_AGUARDANDO, tecnico_id)

        for outra in SolicitacaoTecnico.listar_pendentes_por_servico(servico.id, excluir_id=solicitacao.id):
            outra.marcar_recusada()

        RegistrarNotificacaoService.executar(
            servico.cliente_id,
            "cliente",
            NOTIFICACAO_TECNICO_DEFINIDO,
            "Técnico definido",
            f"Um técnico assumiu o chamado {servico.codigo} ({servico.titulo}).",
            servico.id,
        )

        return solicitacao
