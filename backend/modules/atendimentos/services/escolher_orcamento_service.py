from constants import ORCAMENTO_PENDENTE, STATUS_AGUARDANDO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.atendimentos.models.atendimento import Atendimento
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class EscolherOrcamentoService:
    """Ação do cliente ao decidir qual orçamento aceitar: atribui o técnico
    ao chamado (reaproveitando Servico.atribuir_tecnico, o mesmo método do
    fluxo antigo de aceite direto), avança o status e registra no
    histórico (reaproveitando HistoricoServico). Os demais técnicos que
    enviaram solicitação/orçamento pro mesmo chamado são recusados
    automaticamente — a única forma de "notificação" hoje é a mudança de
    status, sem push/e-mail externo."""

    def executar(self, atendimento_id, cliente):
        atendimento = Atendimento.buscar_por_id(atendimento_id)
        if atendimento is None:
            raise RecursoNaoEncontradoError("Orçamento não encontrado.")

        servico = atendimento.servico
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode escolher um orçamento.")
        if atendimento.status != ORCAMENTO_PENDENTE:
            raise ValidacaoError("Este orçamento já foi decidido.")
        if servico.tecnico_id is not None:
            raise ValidacaoError("Este chamado já tem um técnico atribuído.")

        atendimento.marcar_aceito()

        for outro in Atendimento.listar_por_servico(servico.id):
            if outro.id != atendimento.id and outro.status == ORCAMENTO_PENDENTE:
                outro.marcar_recusado()

        solicitacao_vencedora = SolicitacaoTecnico.buscar_por_servico_e_tecnico(servico.id, atendimento.tecnico_id)
        if solicitacao_vencedora:
            solicitacao_vencedora.marcar_aceita()

        for outra in SolicitacaoTecnico.listar_abertas_por_servico(servico.id, excluir_tecnico_id=atendimento.tecnico_id):
            outra.marcar_recusada()

        status_anterior = servico.status
        servico.atribuir_tecnico(atendimento.tecnico_id, STATUS_AGUARDANDO)
        HistoricoServico.registrar(servico.id, status_anterior, STATUS_AGUARDANDO, cliente.id)

        return servico
