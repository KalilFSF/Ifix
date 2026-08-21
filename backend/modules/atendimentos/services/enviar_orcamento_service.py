from constants import ORCAMENTO_PENDENTE, SOLICITACAO_PENDENTE
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, SolicitacaoJaRespondidaError, ValidacaoError
from modules.atendimentos.models.atendimento import Atendimento
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
        dados_atendimento = {
            "titulo": "Orçamento",
            "descricao": observacoes or "Orçamento enviado pelo técnico.",
            "status": ORCAMENTO_PENDENTE,
            "valor_orcamento": valor_orcamento,
            "prazo_estimado_dias": prazo_estimado_dias,
            "cliente_id": servico.cliente_id,
        }

        atendimento_existente = Atendimento.buscar_por_servico_e_tecnico(servico.id, tecnico_id)
        if atendimento_existente:
            atendimento = atendimento_existente.atualizar(dados_atendimento)
        else:
            atendimento = Atendimento.criar(dados_atendimento, servico.id, tecnico_id, "tecnico")

        solicitacao.marcar_orcamento_enviado()
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
