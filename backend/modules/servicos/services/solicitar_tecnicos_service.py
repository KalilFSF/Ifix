from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico


class SolicitarTecnicosService:
    """Oferece um chamado a um ou mais técnicos. Ponto de extensão para a
    futura automação n8n/IA: quando a análise automática existir, ela vai
    chamar isto (ou um endpoint equivalente autenticado como serviço)
    depois de decidir quais técnicos notificar."""

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
        return criadas
