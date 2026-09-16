from constants import (
    RAIO_AMPLIACAO_MAXIMO_KM,
    RAIO_SELECAO_TECNICOS_KM,
    STATUS_ABERTO,
)
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.servicos.services.selecionar_tecnicos_service import SelecionarTecnicosService
from modules.servicos.services.solicitar_tecnicos_service import SolicitarTecnicosService


class AmpliarBuscaTecnicosService:
    """Amplia manualmente o alcance da busca por técnicos de um chamado que
    ainda não recebeu ninguém.

    A expansão automática de SelecionarTecnicosService só dispara quando há
    menos de TECNICOS_SELECIONADOS_MIN candidatos — ou seja, ela resolve
    "não achei ninguém", mas não resolve "achei dois e nenhum respondeu".
    Esse segundo caso é justamente o que deixava o cliente parado, sem nada
    para fazer além de esperar. Aqui ele dobra o raio por conta própria, e
    só entram técnicos que ainda não foram acionados neste chamado.
    """

    def __init__(self):
        self.selecionar_tecnicos_service = SelecionarTecnicosService()
        self.solicitar_tecnicos_service = SolicitarTecnicosService()

    def executar(self, servico_id, cliente):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.cliente_id != cliente.id:
            raise PermissaoNegadaError("Apenas o cliente dono do chamado pode ampliar a busca.")
        if servico.status != STATUS_ABERTO:
            raise ValidacaoError("Este chamado já tem técnico definido — não há busca para ampliar.")
        if servico.latitude is None or servico.longitude is None:
            raise ValidacaoError(
                "Este chamado não tem localização, então não dá para medir distância. "
                "Atualize sua localização no perfil e abra o chamado novamente."
            )

        raio_atual = servico.raio_busca_km or RAIO_SELECAO_TECNICOS_KM
        if raio_atual >= RAIO_AMPLIACAO_MAXIMO_KM:
            raise ValidacaoError(
                f"A busca já está no alcance máximo de {RAIO_AMPLIACAO_MAXIMO_KM} km."
            )

        novo_raio = min(raio_atual * 2, RAIO_AMPLIACAO_MAXIMO_KM)
        servico.ampliar_raio_busca(novo_raio)

        ja_acionados = SolicitacaoTecnico.listar_ids_tecnicos_do_servico(servico.id)
        tecnico_ids = self.selecionar_tecnicos_service.executar(
            servico, raio_inicial_km=novo_raio, ignorar_ids=ja_acionados
        )

        if tecnico_ids:
            self.solicitar_tecnicos_service.executar(servico.id, tecnico_ids, cliente)

        return {"raio_km": novo_raio, "tecnicos_notificados": len(tecnico_ids)}
