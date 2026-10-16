from constants import (
    MAX_ORCAMENTOS_POR_CHAMADO,
    NOTIFICACAO_ORCAMENTO_RECEBIDO,
    ORCAMENTO_PENDENTE,
    SOLICITACAO_PENDENTE,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError, ValidacaoError
from modules.atendimentos.models.atendimento import Atendimento
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class EnviarOrcamentoService:
    """Ação do técnico ao analisar uma solicitação pendente: em vez de
    simplesmente aceitar, envia valor + prazo + observações. Fica registrado
    como Atendimento (reaproveitando a Model já usada pra "orçamento ligado
    a um chamado"). Vários técnicos podem enviar orçamento pro mesmo
    chamado — quem assume de fato só é decidido depois, pelo cliente
    (EscolherOrcamentoService)."""

    def executar(self, solicitacao_id, tecnico_id, dados):
        solicitacao = SolicitacaoTecnico.buscar_por_id(solicitacao_id)
        if solicitacao is None:
            raise RecursoNaoEncontradoError("Solicitação não encontrada.")
        if solicitacao.tecnico_id != tecnico_id:
            raise PermissaoNegadaError("Esta solicitação não pertence a este técnico.")
        if solicitacao.status != SOLICITACAO_PENDENTE:
            raise SolicitacaoJaRespondidaError("Esta solicitação já foi respondida.")

        valor_orcamento = self._parse_valor(dados.get("valor_orcamento"))
        prazo_estimado_dias = self._parse_prazo(dados.get("prazo_estimado_dias"))
        observacoes = (dados.get("observacoes") or "").strip()

        servico = solicitacao.servico
        atendimento_existente = Atendimento.buscar_por_servico_e_tecnico(servico.id, tecnico_id)

        # Comparativo de propostas (funcionalidade 8): o cliente compara no
        # máximo MAX_ORCAMENTOS_POR_CHAMADO. O limite só barra um técnico
        # novo — quem já tem orçamento no chamado não é contado de novo.
        if atendimento_existente is None and Atendimento.contar_orcamentos_do_servico(servico.id) >= MAX_ORCAMENTOS_POR_CHAMADO:
            raise ValidacaoError(
                f"Este chamado já recebeu o máximo de {MAX_ORCAMENTOS_POR_CHAMADO} orçamentos."
            )

        # Teto de gasto (funcionalidade 6): orçamento acima do limite do
        # cliente é permitido, mas fica marcado — bloquear aqui deixaria um
        # chamado de teto baixo sem nenhum orçamento, e quem decide se o
        # valor vale a pena é o cliente, na hora de escolher.
        acima_do_teto = not servico.cabe_no_teto(valor_orcamento)

        dados_atendimento = {
            "titulo": "Orçamento acima do teto" if acima_do_teto else "Orçamento",
            "descricao": observacoes or "Orçamento enviado pelo técnico.",
            "status": ORCAMENTO_PENDENTE,
            "valor_orcamento": valor_orcamento,
            "prazo_estimado_dias": prazo_estimado_dias,
            "cliente_id": servico.cliente_id,
        }

        if atendimento_existente:
            atendimento = atendimento_existente.atualizar(dados_atendimento)
        else:
            atendimento = Atendimento.criar(dados_atendimento, servico.id, tecnico_id, "tecnico")

        solicitacao.marcar_orcamento_enviado()
        RegistrarNotificacaoService.executar(
            servico.cliente_id,
            "cliente",
            NOTIFICACAO_ORCAMENTO_RECEBIDO,
            "Novo orçamento",
            f"Você recebeu um orçamento para o chamado {servico.codigo} ({servico.titulo}).",
            servico.id,
        )
        return atendimento

    @staticmethod
    def _parse_valor(valor):
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um valor de orçamento válido.")
        if valor <= 0:
            raise ValidacaoError("O valor do orçamento deve ser maior que zero.")
        return valor

    @staticmethod
    def _parse_prazo(prazo):
        if prazo in (None, ""):
            return None
        try:
            prazo = int(prazo)
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um prazo estimado válido (em dias).")
        if prazo <= 0:
            raise ValidacaoError("O prazo estimado deve ser maior que zero.")
        return prazo
