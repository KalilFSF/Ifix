"""Encaminha a atribuição legada ao aceite de convite autorizado, sem permitir apropriação."""
from transactions import atomic,lock_model
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.servicos.services.aceitar_solicitacao_service import AceitarSolicitacaoService
from exceptions import RecursoNaoEncontradoError

class AtribuirTecnicoService:
    @atomic
    def executar(self,servico_id,tecnico_id):
        servico = lock_model(Servico,servico_id)
        convite = SolicitacaoTecnico.buscar_pendente(servico_id,tecnico_id) if servico else None
        if convite is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        AceitarSolicitacaoService().executar(convite.id,tecnico_id)
        return servico
