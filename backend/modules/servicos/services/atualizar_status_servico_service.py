from constants import (
    NOTIFICACAO_STATUS,
    STATUS_CLIENTE_CHOICES,
    STATUS_FINALIZADO,
    STATUS_LABELS_EMAIL,
    STATUS_MINIMO_PARA_FINALIZAR,
    STATUS_TECNICO_CHOICES,
    STATUS_TERMINAIS,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.aprovacao import SolicitacaoAprovacao
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico
from services.email_service import EmailService


class AtualizarStatusServicoService:
    """Transição de status do chamado, com o conjunto de destinos permitidos
    dependendo de QUEM está pedindo (ver STATUS_TECNICO_CHOICES e
    STATUS_CLIENTE_CHOICES em constants.py):

    - técnico responsável: conduz o reparo e pode concluí-lo;
    - cliente dono: pode confirmar a conclusão ("finalizado").

    As duas travas de finalização (autorização de custo pendente e laudo
    ausente) valem para os dois participantes."""

    def executar(self, servico_id, novo_status, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")

        eh_tecnico_do_chamado = servico.tecnico_id is not None and servico.tecnico_id == usuario.id
        eh_cliente_do_chamado = servico.cliente_id == usuario.id

        if eh_tecnico_do_chamado:
            permitidos = STATUS_TECNICO_CHOICES
        elif eh_cliente_do_chamado:
            permitidos = STATUS_CLIENTE_CHOICES
        else:
            raise PermissaoNegadaError("Apenas o cliente e o técnico deste chamado podem alterá-lo.")

        if servico.status in STATUS_TERMINAIS:
            raise ValidacaoError("Este chamado já foi encerrado e não pode mudar de status.")

        if novo_status not in permitidos:
            raise ValidacaoError(self._motivo_status_negado(novo_status))

        if novo_status == STATUS_FINALIZADO:
            self._validar_conclusao(servico, eh_tecnico_do_chamado)

        status_anterior = servico.status
        servico.atualizar_status(novo_status)
        HistoricoServico.registrar(servico.id, status_anterior, novo_status, usuario.id)
        self._notificar_outro_participante(servico, novo_status, usuario)
        return servico

    @staticmethod
    def _motivo_status_negado(novo_status):
        return f"Status inválido: {novo_status}"

    @staticmethod
    def _validar_conclusao(servico, eh_tecnico):
        if servico.status != STATUS_MINIMO_PARA_FINALIZAR:
            raise ValidacaoError(
                "O chamado só pode ser concluído depois que o técnico colocá-lo em reparo."
            )
        # Funcionalidades 6 e 7: concluir com pedido pendente daria por
        # encerrado um serviço com custo que ninguém autorizou.
        if SolicitacaoAprovacao.buscar_pendente_do_servico(servico.id):
            mensagem = (
                "Aguarde o cliente responder à autorização de custo pendente antes de concluir o chamado."
                if eh_tecnico
                else "Responda à autorização de custo pendente antes de concluir o chamado."
            )
            raise ValidacaoError(mensagem)
        # Sem isso o cliente ficaria sem explicação nenhuma do que houve com o
        # aparelho, e a reincidência por modelo (funcionalidade 10) não teria
        # dado nenhum pra agregar.
        if not servico.tem_laudo:
            mensagem = (
                "Registre o relatório técnico antes de concluir o chamado."
                if eh_tecnico
                else "O técnico ainda não enviou o relatório técnico. Aguarde a conclusão do reparo."
            )
            raise ValidacaoError(mensagem)

    @staticmethod
    def _notificar_outro_participante(servico, novo_status, autor):
        """Quem recebe o aviso é sempre o outro lado do chamado."""
        autor_eh_cliente = autor.id == servico.cliente_id
        destinatario = servico.tecnico if autor_eh_cliente else servico.cliente
        if not destinatario:
            return

        rotulo = STATUS_LABELS_EMAIL.get(novo_status, novo_status)
        RegistrarNotificacaoService.executar(
            destinatario.id,
            "tecnico" if autor_eh_cliente else "cliente",
            NOTIFICACAO_STATUS,
            f"Chamado {rotulo.lower()}",
            f"O chamado {servico.codigo} ({servico.titulo}) agora está: {rotulo}.",
            servico.id,
        )
        if not destinatario.email:
            return

        corpo_html = f"""
            <p>Olá, {destinatario.nome}!</p>
            <p>O status do chamado <strong>{servico.codigo}</strong> ({servico.titulo}) foi atualizado:</p>
            <p style="font-size:18px;"><strong>{rotulo}</strong></p>
            <p>Acesse sua conta no iFix pra ver os detalhes e o histórico completo.</p>
        """
        EmailService.enviar_email(
            destinatario.email, destinatario.nome, f"Chamado {servico.codigo} — {rotulo}", corpo_html
        )
