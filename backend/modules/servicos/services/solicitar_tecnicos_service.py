from datetime import datetime

from constants import NOTIFICACAO_NOVA_SOLICITACAO, URGENCIA_PRAZO_HORAS
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.notificacoes.services.registrar_notificacao_service import RegistrarNotificacaoService
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.usuarios.models.usuario import Usuario
from services.email_service import EmailService
from utils import horario_dentro_da_faixa


class SolicitarTecnicosService:
    """Oferece um chamado a um ou mais técnicos. Ponto de extensão para a
    futura automação n8n/IA: quando a análise automática existir, ela vai
    chamar isto (ou um endpoint equivalente autenticado como serviço)
    depois de decidir quais técnicos notificar.

    A solicitação em si é sempre criada — a restrição de horário
    (funcionalidade 9) filtra só o e-mail de aviso, nunca o acesso ao
    chamado: bloquear a solicitação deixaria o cliente sem atendimento por
    um motivo que é do técnico, e o resto do sistema é construído pra nunca
    deixar um chamado sem ninguém notificado."""

    def executar(self, servico_id, tecnico_ids, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != usuario.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode solicitar técnicos.")

        criadas = []
        for tecnico_id in tecnico_ids:
            if SolicitacaoTecnico.buscar_pendente(servico_id, tecnico_id):
                continue
            criadas.append(SolicitacaoTecnico.criar(servico_id, tecnico_id))
            self._avisar_no_app(servico, tecnico_id)
            self._notificar_tecnico(servico, tecnico_id)
        return criadas

    @staticmethod
    def _avisar_no_app(servico, tecnico_id):
        # O aviso no app não passa pela restrição de horário: ele não
        # interrompe ninguém, só espera o técnico abrir o painel.
        urgencia = "URGENTE — " if servico.urgente else ""
        RegistrarNotificacaoService.executar(
            tecnico_id,
            "tecnico",
            NOTIFICACAO_NOVA_SOLICITACAO,
            f"{urgencia}Nova solicitação",
            f"Chamado {servico.codigo} ({servico.titulo}) aguarda o seu orçamento.",
            servico.id,
        )

    @staticmethod
    def _notificar_tecnico(servico, tecnico_id):
        tecnico = Usuario.buscar_por_id(tecnico_id)
        if not tecnico or not tecnico.email:
            return

        agora = datetime.now().time()
        # Urgência (funcionalidade 1) fura a restrição de horário: o cliente
        # pagou por resposta em até URGENCIA_PRAZO_HORAS, e um e-mail
        # suprimido de madrugada comeria esse prazo.
        if not servico.urgente and not horario_dentro_da_faixa(
            agora, tecnico.horario_inicio_atendimento, tecnico.horario_fim_atendimento
        ):
            # Fora da faixa que o técnico configurou: a solicitação continua
            # no painel dele, só não recebe o e-mail agora.
            return

        if servico.urgente:
            aviso_urgencia = (
                f"<p><strong>ATENDIMENTO DE URGÊNCIA:</strong> o cliente espera atendimento em até "
                f"{URGENCIA_PRAZO_HORAS} horas depois de escolher o técnico.</p>"
            )
            assunto = f"URGENTE — Nova solicitação de chamado — {servico.codigo}"
        else:
            aviso_urgencia = ""
            assunto = f"Nova solicitação de chamado — {servico.codigo}"

        corpo_html = f"""
            <p>Olá, {tecnico.nome}!</p>
            <p>Você recebeu uma nova solicitação de chamado no iFix:
               <strong>{servico.codigo}</strong> ({servico.titulo}).</p>
            {aviso_urgencia}
            <p>Acesse seu painel para ver os detalhes e enviar um orçamento.</p>
        """
        EmailService.enviar_email(tecnico.email, tecnico.nome, assunto, corpo_html)
