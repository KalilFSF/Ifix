from constants import STATUS_LABELS_EMAIL, STATUS_TECNICO_CHOICES
from email_service import enviar_email
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico


class AtualizarStatusServicoService:
    def executar(self, servico_id, novo_status, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if novo_status not in STATUS_TECNICO_CHOICES:
            raise ValidacaoError(f"Status inválido: {novo_status}")
        if servico.tecnico_id != usuario.id:
            raise PermissaoNegadaError("Apenas o técnico responsável pode atualizar este chamado.")

        status_anterior = servico.status
        servico.atualizar_status(novo_status)
        HistoricoServico.registrar(servico.id, status_anterior, novo_status, usuario.id)
        self._notificar_cliente(servico, novo_status)
        return servico

    @staticmethod
    def _notificar_cliente(servico, novo_status):
        cliente = servico.cliente
        if not cliente or not cliente.email:
            return

        rotulo = STATUS_LABELS_EMAIL.get(novo_status, novo_status)
        corpo_html = f"""
            <p>Olá, {cliente.nome}!</p>
            <p>O status do seu chamado <strong>{servico.codigo}</strong> ({servico.titulo}) foi atualizado:</p>
            <p style="font-size:18px;"><strong>{rotulo}</strong></p>
            <p>Acesse sua conta no iFix pra ver os detalhes e o histórico completo.</p>
        """
        enviar_email(cliente.email, cliente.nome, f"Chamado {servico.codigo} — {rotulo}", corpo_html)
