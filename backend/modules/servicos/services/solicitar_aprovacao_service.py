from constants import (
    MIN_CARACTERES_DESCRICAO_APROVACAO,
    NOTIFICACAO_AUTORIZACAO_PEDIDA,
    STATUS_ABERTO,
    STATUS_AGUARDANDO,
    STATUS_CANCELADO,
    STATUS_FINALIZADO,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.aprovacao import SolicitacaoAprovacao
from modules.servicos.models.servico import Servico
from services.email_service import EmailService
from utils import formatar_moeda_brl


class SolicitarAprovacaoService:
    """Técnico pede autorização pra um custo adicional (funcionalidade 7).

    Encontrou um problema novo no meio do reparo? Não executa por conta
    própria: descreve o que achou, diz quanto custa a mais e espera o
    cliente autorizar. É isso que dá dente ao teto de gasto da
    funcionalidade 6 — enquanto o pedido estiver pendente,
    AtualizarStatusServicoService não deixa finalizar o chamado.

    Só um pedido pendente por vez, pra não empilhar autorizações que o
    cliente responderia fora de ordem."""

    def executar(self, servico_id, tecnico, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.tecnico_id != tecnico.id:
            raise PermissaoNegadaError("Apenas o técnico responsável pode solicitar autorização.")
        if servico.status in (STATUS_ABERTO, STATUS_AGUARDANDO):
            raise ValidacaoError("Inicie o atendimento antes de solicitar autorização de custo.")
        if servico.status in (STATUS_FINALIZADO, STATUS_CANCELADO):
            raise ValidacaoError("Este chamado já foi encerrado.")
        if SolicitacaoAprovacao.buscar_pendente_do_servico(servico_id):
            raise ValidacaoError("Já existe uma autorização aguardando resposta do cliente.")

        descricao = self._parse_descricao(dados.get("descricao"))
        valor = self._parse_valor(dados.get("valor_adicional"))

        aprovacao = SolicitacaoAprovacao.criar(servico_id, tecnico.id, descricao, valor)
        RegistrarNotificacaoService.executar(
            servico.cliente_id,
            "cliente",
            NOTIFICACAO_AUTORIZACAO_PEDIDA,
            "Autorização necessária",
            f"O técnico pediu autorização de {formatar_moeda_brl(valor)} extras no chamado {servico.codigo}.",
            servico.id,
        )
        self._notificar_cliente(servico, aprovacao)
        return aprovacao

    @staticmethod
    def _parse_descricao(valor):
        descricao = (valor or "").strip()
        if len(descricao) < MIN_CARACTERES_DESCRICAO_APROVACAO:
            raise ValidacaoError(
                "Descreva o problema encontrado com pelo menos "
                f"{MIN_CARACTERES_DESCRICAO_APROVACAO} caracteres."
            )
        return descricao

    @staticmethod
    def _parse_valor(valor):
        try:
            valor_adicional = float(valor)
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um valor adicional válido.")
        if valor_adicional <= 0:
            raise ValidacaoError("O valor adicional deve ser maior que zero.")
        return round(valor_adicional, 2)

    @staticmethod
    def _notificar_cliente(servico, aprovacao):
        cliente = servico.cliente
        if not cliente or not cliente.email:
            return

        corpo_html = f"""
            <p>Olá, {cliente.nome}!</p>
            <p>O técnico encontrou um problema adicional no seu chamado
               <strong>{servico.codigo}</strong> ({servico.titulo}) e precisa da sua
               autorização para continuar:</p>
            <p>{aprovacao.descricao}</p>
            <p style="font-size:18px;"><strong>Custo adicional:
               {formatar_moeda_brl(aprovacao.valor_adicional)}</strong></p>
            <p>Nada será executado sem a sua aprovação. Acesse sua conta no iFix
               para autorizar ou recusar.</p>
        """
        EmailService.enviar_email(
            cliente.email,
            cliente.nome,
            f"Chamado {servico.codigo} — autorização necessária",
            corpo_html,
        )
