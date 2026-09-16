from constants import STATUS_AGUARDANDO
from exceptions import RecursoNaoEncontradoError
from modules.servicos.models.servico import Servico


class AtribuirTecnicoService:
    """Legado: atribuição direta e irrestrita de um técnico a um chamado
    aberto (POST /api/servicos/<id>/aceitar), sem passar pelo fluxo de
    solicitação/aceite. Não é mais chamada por nenhuma tela — o painel do
    técnico usa AceitarSolicitacaoService — mas o endpoint continua
    registrado por compatibilidade, então a operação continua existindo."""

    def executar(self, servico_id, tecnico_id):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        # STATUS_AGUARDANDO, e não a string "em_andamento" que estava aqui:
        # aquele valor não existe em constants.py nem nos rótulos do front,
        # então o chamado ficava com badge de texto cru e o stepper inteiro
        # em "etapa futura", sem nenhuma etapa marcada como atual.
        return servico.atribuir_tecnico(tecnico_id, STATUS_AGUARDANDO)
