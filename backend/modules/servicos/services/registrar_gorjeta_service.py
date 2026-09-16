from constants import STATUS_FINALIZADO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.servico import Servico
from services.email_service import EmailService
from utils import formatar_moeda_brl


class RegistrarGorjetaService:
    """Gorjeta opcional do cliente ao técnico, depois do chamado concluído.

    PAGAMENTO: aqui só registramos o valor e avisamos o técnico — a cobrança
    depende do meio de pagamento, que ainda não existe no sistema (mesmo
    ponto de extensão marcado em constants.py, antes de STATUS_FINALIZADO).
    Por isso a gorjeta é combinada diretamente entre os dois, e o registro
    serve de acordo explícito, não de cobrança.
    """

    def executar(self, servico_id, cliente, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente do chamado pode deixar uma gorjeta.")
        if servico.status != STATUS_FINALIZADO:
            raise ValidacaoError("A gorjeta só pode ser registrada depois que o chamado for concluído.")
        if servico.tecnico_id is None:
            raise ValidacaoError("Este chamado não teve técnico atribuído.")
        if servico.tem_gorjeta:
            raise ValidacaoError("Você já registrou uma gorjeta neste chamado.")

        valor = self._parse_valor(dados.get("valor"))
        servico.registrar_gorjeta(valor)
        self._notificar_tecnico(servico, valor)
        return servico

    @staticmethod
    def _parse_valor(valor):
        try:
            numero = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um valor de gorjeta válido.") from None
        if numero <= 0:
            raise ValidacaoError("A gorjeta precisa ser maior que zero.")
        return round(numero, 2)

    @staticmethod
    def _notificar_tecnico(servico, valor):
        tecnico = servico.tecnico
        if not tecnico or not tecnico.email:
            return

        corpo_html = f"""
            <p>Olá, {tecnico.nome}!</p>
            <p>O cliente do chamado <strong>{servico.codigo}</strong> ({servico.titulo})
               deixou uma gorjeta de <strong>{formatar_moeda_brl(valor)}</strong>
               como reconhecimento pelo atendimento.</p>
            <p>O iFix ainda não processa pagamentos, então combine o repasse
               diretamente com o cliente.</p>
        """
        EmailService.enviar_email(
            tecnico.email, tecnico.nome,
            f"Gorjeta no chamado {servico.codigo}", corpo_html,
        )
