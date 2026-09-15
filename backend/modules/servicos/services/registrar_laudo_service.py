from constants import (
    CAUSAS_DEFEITO,
    CAUSAS_DEFEITO_LABELS,
    MIN_CARACTERES_LAUDO,
    STATUS_ABERTO,
    STATUS_AGUARDANDO,
    STATUS_CANCELADO,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.servico import Servico
from services.email_service import EmailService


class RegistrarLaudoService:
    """Relatório técnico simplificado (funcionalidade 8): o técnico registra a
    causa do defeito, a explicação em linguagem de cliente e o que foi feito
    pra resolver.

    A causa vem de um catálogo fechado (constants.CAUSAS_DEFEITO) em vez de
    texto livre porque é ela que permite detectar reincidência de um mesmo
    defeito por modelo de aparelho — texto livre não agrupa.

    Pode ser registrado (e corrigido) enquanto o chamado está em andamento;
    AtualizarStatusServicoService exige que exista antes de finalizar."""

    def executar(self, servico_id, usuario, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.tecnico_id != usuario.id:
            raise PermissaoNegadaError("Apenas o técnico responsável pode registrar o laudo.")
        if servico.status in (STATUS_ABERTO, STATUS_AGUARDANDO):
            raise ValidacaoError("Inicie a análise do chamado antes de registrar o laudo.")
        if servico.status == STATUS_CANCELADO:
            raise ValidacaoError("Não é possível registrar laudo em um chamado cancelado.")

        causa = self._parse_causa(dados.get("causa_defeito"))
        laudo = self._parse_laudo(dados.get("laudo_tecnico"))
        solucao = (dados.get("solucao_aplicada") or "").strip() or None

        era_primeiro_laudo = not servico.tem_laudo
        servico.registrar_laudo(causa, laudo, solucao)
        if era_primeiro_laudo:
            self._notificar_cliente(servico)
        return servico

    @staticmethod
    def _parse_causa(valor):
        causa = (valor or "").strip().lower()
        if causa not in CAUSAS_DEFEITO:
            raise ValidacaoError("Selecione uma causa de defeito válida.")
        return causa

    @staticmethod
    def _parse_laudo(valor):
        laudo = (valor or "").strip()
        if len(laudo) < MIN_CARACTERES_LAUDO:
            raise ValidacaoError(
                f"Explique a causa do defeito com pelo menos {MIN_CARACTERES_LAUDO} caracteres."
            )
        return laudo

    @staticmethod
    def _notificar_cliente(servico):
        cliente = servico.cliente
        if not cliente or not cliente.email:
            return

        rotulo_causa = CAUSAS_DEFEITO_LABELS.get(servico.causa_defeito, servico.causa_defeito)
        corpo_html = f"""
            <p>Olá, {cliente.nome}!</p>
            <p>O técnico registrou o relatório técnico do seu chamado
               <strong>{servico.codigo}</strong> ({servico.titulo}).</p>
            <p><strong>Causa identificada:</strong> {rotulo_causa}</p>
            <p>Acesse sua conta no iFix pra ler a explicação completa.</p>
        """
        EmailService.enviar_email(
            cliente.email,
            cliente.nome,
            f"Chamado {servico.codigo} — relatório técnico disponível",
            corpo_html,
        )
