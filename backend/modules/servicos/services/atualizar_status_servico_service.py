from constants import (
    STATUS_CLIENTE_CHOICES,
    STATUS_FINALIZADO,
    STATUS_LABELS_EMAIL,
    STATUS_MINIMO_PARA_FINALIZAR,
    STATUS_TECNICO_CHOICES,
    STATUS_TERMINAIS,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.aprovacao import SolicitacaoAprovacao
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico
from services.email_service import EmailService


class AtualizarStatusServicoService:
    """Transição de status do chamado, com o conjunto de destinos permitidos
    dependendo de QUEM está pedindo (ver STATUS_TECNICO_CHOICES e
    STATUS_CLIENTE_CHOICES em constants.py):

    - técnico responsável: conduz o reparo até "em reparo";
    - cliente dono: confirma a conclusão ("finalizado"), e só ele.

    As duas travas de finalização (autorização de custo pendente e laudo
    ausente) continuam valendo, mas agora são lidas pelo cliente — por isso
    as mensagens são escritas na voz dele."""

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
            raise ValidacaoError(self._motivo_status_negado(novo_status, eh_tecnico_do_chamado))

        if novo_status == STATUS_FINALIZADO:
            self._validar_conclusao(servico)

        status_anterior = servico.status
        servico.atualizar_status(novo_status)
        HistoricoServico.registrar(servico.id, status_anterior, novo_status, usuario.id)
        self._notificar_outro_participante(servico, novo_status, usuario)
        return servico

    @staticmethod
    def _motivo_status_negado(novo_status, eh_tecnico):
        if novo_status == STATUS_FINALIZADO and eh_tecnico:
            return (
                "A conclusão do chamado é confirmada pelo cliente. "
                "Deixe o chamado em reparo e registre o laudo técnico."
            )
        return f"Status inválido: {novo_status}"

    @staticmethod
    def _validar_conclusao(servico):
        if servico.status != STATUS_MINIMO_PARA_FINALIZAR:
            raise ValidacaoError(
                "O chamado só pode ser concluído depois que o técnico colocá-lo em reparo."
            )
        # A autorização pendente vem primeiro de propósito: ela depende de uma
        # ação do próprio cliente, então é o que ele resolve agora. O laudo
        # depende do técnico, e ele não tem o que fazer além de esperar.
        # Funcionalidades 6 e 7: concluir com pedido pendente daria por
        # encerrado um serviço com custo que ninguém autorizou.
        if SolicitacaoAprovacao.buscar_pendente_do_servico(servico.id):
            raise ValidacaoError(
                "Responda à autorização de custo pendente antes de concluir o chamado."
            )
        # Sem isso o cliente ficaria sem explicação nenhuma do que houve com o
        # aparelho, e a reincidência por modelo (funcionalidade 10) não teria
        # dado nenhum pra agregar.
        if not servico.tem_laudo:
            raise ValidacaoError(
                "O técnico ainda não enviou o relatório técnico. Aguarde a conclusão do reparo."
            )

    @staticmethod
    def _notificar_outro_participante(servico, novo_status, autor):
        """Quem recebe o aviso é sempre o outro lado — se o cliente finaliza,
        mandar o e-mail pra ele mesmo não informaria ninguém."""
        destinatario = servico.tecnico if autor.id == servico.cliente_id else servico.cliente
        if not destinatario or not destinatario.email:
            return

        rotulo = STATUS_LABELS_EMAIL.get(novo_status, novo_status)
        corpo_html = f"""
            <p>Olá, {destinatario.nome}!</p>
            <p>O status do chamado <strong>{servico.codigo}</strong> ({servico.titulo}) foi atualizado:</p>
            <p style="font-size:18px;"><strong>{rotulo}</strong></p>
            <p>Acesse sua conta no iFix pra ver os detalhes e o histórico completo.</p>
        """
        EmailService.enviar_email(
            destinatario.email, destinatario.nome, f"Chamado {servico.codigo} — {rotulo}", corpo_html
        )
