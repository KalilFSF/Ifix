from constants import APROVACAO_APROVADA, APROVACAO_STATUS_RESPOSTA, NOTIFICACAO_AUTORIZACAO_RESPONDIDA
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.aprovacao import SolicitacaoAprovacao
from services.email_service import EmailService
from utils import formatar_moeda_brl


class ResponderAprovacaoService:
    """Cliente autoriza ou recusa remotamente a continuidade do serviço
    (funcionalidade 7), sem precisar estar presente onde o aparelho está.

    Aprovar eleva o teto de gasto do chamado no valor autorizado — assim o
    limite continua valendo pro que vier depois, em vez de virar um cheque
    em branco a partir da primeira autorização."""

    def executar(self, aprovacao_id, cliente, dados):
        aprovacao = SolicitacaoAprovacao.buscar_por_id(aprovacao_id)
        if aprovacao is None:
            raise RecursoNaoEncontradoError("Solicitação de autorização não encontrada.")

        servico = aprovacao.servico
        if servico is None or servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode responder.")
        if not aprovacao.pendente:
            raise ValidacaoError("Esta autorização já foi respondida.")

        status = (dados.get("status") or "").strip().lower()
        if status not in APROVACAO_STATUS_RESPOSTA:
            raise ValidacaoError("Informe se autoriza ou recusa a continuidade.")

        if status == APROVACAO_APROVADA:
            aprovacao.aprovar()
            servico.elevar_teto(aprovacao.valor_adicional)
        else:
            aprovacao.recusar((dados.get("justificativa_recusa") or "").strip() or None)

        RegistrarNotificacaoService.executar(
            aprovacao.tecnico_id,
            "tecnico",
            NOTIFICACAO_AUTORIZACAO_RESPONDIDA,
            "Custo adicional " + ("autorizado" if status == APROVACAO_APROVADA else "recusado"),
            f"O cliente respondeu ao pedido de custo adicional do chamado {servico.codigo}.",
            servico.id,
        )
        self._notificar_tecnico(servico, aprovacao)
        return aprovacao

    @staticmethod
    def _notificar_tecnico(servico, aprovacao):
        tecnico = aprovacao.tecnico
        if not tecnico or not tecnico.email:
            return

        autorizado = aprovacao.status == APROVACAO_APROVADA
        titulo = "autorizado" if autorizado else "recusado"
        complemento = (
            "<p>Você já pode executar o reparo adicional.</p>"
            if autorizado
            else "<p>Não execute o reparo adicional. Finalize o chamado com o que foi acordado.</p>"
        )
        if not autorizado and aprovacao.justificativa_recusa:
            complemento += f"<p><strong>Motivo do cliente:</strong> {aprovacao.justificativa_recusa}</p>"

        corpo_html = f"""
            <p>Olá, {tecnico.nome}!</p>
            <p>O cliente <strong>{titulo}</strong> o custo adicional de
               {formatar_moeda_brl(aprovacao.valor_adicional)} no chamado
               <strong>{servico.codigo}</strong> ({servico.titulo}).</p>
            {complemento}
        """
        EmailService.enviar_email(
            tecnico.email,
            tecnico.nome,
            f"Chamado {servico.codigo} — custo adicional {titulo}",
            corpo_html,
        )
