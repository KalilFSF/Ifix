from constants import STATUS_ABERTO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.usuarios.models.usuario import Usuario
from services.email_service import EmailService
from utils import formatar_moeda_brl


class AumentarTetoServicoService:
    """Eleva o teto de gasto de um chamado que ainda não foi aceito, e avisa
    quem já tinha sido acionado.

    Serve ao caso em que o chamado ficou sem resposta porque o valor não
    compensava o deslocamento: em vez de só esperar, o cliente melhora a
    oferta. Só vale enquanto o chamado está aberto — depois de escolhido um
    orçamento, mudar o teto por fora contornaria a autorização de custo
    adicional (funcionalidades 6 e 7), que existe justamente pra isso.
    """

    def executar(self, servico_id, novo_valor, cliente):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode alterar o valor.")
        if servico.status != STATUS_ABERTO:
            raise ValidacaoError(
                "Este chamado já tem técnico definido. Custos a mais passam pela "
                "autorização de custo adicional."
            )

        valor = self._parse_valor(novo_valor)
        teto_atual = float(servico.valor_maximo_aprovado) if servico.tem_teto else 0.0
        if valor <= teto_atual:
            raise ValidacaoError(
                f"O novo valor precisa ser maior que o atual ({formatar_moeda_brl(teto_atual)})."
            )

        servico.valor_maximo_aprovado = valor
        servico.salvar()

        self._notificar_tecnicos_acionados(servico, valor)
        return servico

    @staticmethod
    def _parse_valor(valor):
        try:
            numero = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um valor válido.") from None
        if numero <= 0:
            raise ValidacaoError("O valor precisa ser maior que zero.")
        return round(numero, 2)

    @staticmethod
    def _notificar_tecnicos_acionados(servico, valor):
        """Aumentar o teto sem avisar ninguém não muda nada: quem já tinha
        visto o chamado e decidido não orçar não voltaria pra olhar de novo."""
        for tecnico_id in SolicitacaoTecnico.listar_ids_tecnicos_do_servico(servico.id):
            tecnico = Usuario.buscar_por_id(tecnico_id)
            if not tecnico or not tecnico.email:
                continue

            corpo_html = f"""
                <p>Olá, {tecnico.nome}!</p>
                <p>O cliente aumentou o valor máximo do chamado
                   <strong>{servico.codigo}</strong> ({servico.titulo}) para
                   <strong>{formatar_moeda_brl(valor)}</strong>.</p>
                <p>Se antes não compensava, vale uma nova olhada no seu painel.</p>
            """
            EmailService.enviar_email(
                tecnico.email, tecnico.nome,
                f"Novo valor no chamado {servico.codigo}", corpo_html,
            )
