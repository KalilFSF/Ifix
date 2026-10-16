from constants import (
    GARANTIA_DIAS,
    GARANTIA_TIPO_NOVO_ATENDIMENTO,
    GARANTIA_TIPOS,
    MIN_CARACTERES_DESCRICAO_GARANTIA,
    STATUS_ABERTO,
    STATUS_AGUARDANDO,
    STATUS_FINALIZADO,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.garantia import AcionamentoGarantia
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import Servico
from services.email_service import EmailService


class AcionarGarantiaService:
    """Acionamento da garantia contratada (funcionalidade 2).

    Quem pagou os +7% na abertura tem GARANTIA_DIAS após a finalização pra
    dizer que o problema voltou. Duas saídas, escolhidas pelo cliente:

    - reembolso: registra o pedido e avisa o técnico; a devolução em si
      depende do meio de pagamento, que ainda não existe no sistema (ver o
      ponto de extensão marcado em constants.py), então o acionamento fica
      como pendente pra tratativa.
    - novo atendimento: abre na hora um chamado novo, gratuito e já
      atribuído ao mesmo técnico que fez o reparo — é ele que tem o
      histórico do aparelho e responde pelo serviço que não resolveu.

    O chamado novo não tem garantia própria: ela já foi paga e consumida no
    chamado original, e renovar a cada acionamento daria garantia infinita.
    """

    def executar(self, servico_id, cliente, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode acionar a garantia.")
        if not servico.garantia:
            raise ValidacaoError("Este chamado não possui garantia contratada.")
        if servico.status != STATUS_FINALIZADO:
            raise ValidacaoError("A garantia só pode ser acionada em um chamado finalizado.")
        if not servico.garantia_ativa:
            raise ValidacaoError(
                f"O prazo de garantia de {GARANTIA_DIAS} dias após a finalização já expirou."
            )
        if AcionamentoGarantia.buscar_em_andamento_do_servico(servico_id):
            raise ValidacaoError("Já existe um acionamento de garantia em andamento para este chamado.")

        descricao = self._parse_descricao(dados.get("descricao_problema"))
        tipo = self._parse_tipo(dados.get("tipo_solicitado"))

        acionamento = AcionamentoGarantia.criar(servico_id, cliente.id, descricao, tipo)

        if tipo == GARANTIA_TIPO_NOVO_ATENDIMENTO:
            servico_novo = self._abrir_chamado_de_garantia(servico, descricao, cliente)
            acionamento.vincular_servico_novo(servico_novo.id)

        self._notificar_tecnico(servico, acionamento)
        return acionamento

    @staticmethod
    def _abrir_chamado_de_garantia(servico, descricao, cliente):
        """Chamado novo herdando equipamento e localização do original, já
        atribuído ao mesmo técnico e sem custo — o cliente não passa de novo
        pela seleção de técnico nem por orçamento."""
        servico_novo = Servico(
            titulo=f"[Garantia] {servico.titulo}",
            descricao=descricao,
            categoria=servico.categoria,
            tipo_equipamento=servico.tipo_equipamento,
            equipamento=servico.equipamento,
            modalidade=servico.modalidade,
            preco_estimado=0,
            valor_maximo_aprovado=0,
            garantia=False,
            latitude=servico.latitude,
            longitude=servico.longitude,
            cliente_id=cliente.id,
            tecnico_id=servico.tecnico_id,
            status=STATUS_AGUARDANDO if servico.tecnico_id else STATUS_ABERTO,
        ).salvar()

        HistoricoServico.registrar(
            servico_novo.id,
            status_anterior=None,
            status_novo=servico_novo.status,
            alterado_por_id=cliente.id,
        )
        return servico_novo

    @staticmethod
    def _parse_descricao(valor):
        descricao = (valor or "").strip()
        if len(descricao) < MIN_CARACTERES_DESCRICAO_GARANTIA:
            raise ValidacaoError(
                "Descreva o que voltou a acontecer com pelo menos "
                f"{MIN_CARACTERES_DESCRICAO_GARANTIA} caracteres."
            )
        return descricao

    @staticmethod
    def _parse_tipo(valor):
        tipo = (valor or "").strip().lower()
        if tipo not in GARANTIA_TIPOS:
            raise ValidacaoError("Escolha entre reembolso ou novo atendimento.")
        return tipo

    @staticmethod
    def _notificar_tecnico(servico, acionamento):
        tecnico = servico.tecnico
        if not tecnico or not tecnico.email:
            return

        if acionamento.tipo_solicitado == GARANTIA_TIPO_NOVO_ATENDIMENTO:
            complemento = (
                "<p>Um chamado novo já foi aberto no seu painel, sem custo para o cliente.</p>"
            )
        else:
            complemento = "<p>O cliente solicitou reembolso. Entre em contato para tratar o caso.</p>"

        corpo_html = f"""
            <p>Olá, {tecnico.nome}!</p>
            <p>O cliente acionou a garantia do chamado <strong>{servico.codigo}</strong>
               ({servico.titulo}).</p>
            <p><strong>O que voltou a acontecer:</strong> {acionamento.descricao_problema}</p>
            {complemento}
        """
        EmailService.enviar_email(
            tecnico.email,
            tecnico.nome,
            f"Garantia acionada — chamado {servico.codigo}",
            corpo_html,
        )
