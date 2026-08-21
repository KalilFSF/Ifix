from modules.servicos.repositories.solicitacao_repository import SolicitacaoRepository


class ListarSolicitacoesPendentesService:
    def __init__(self):
        self.solicitacao_repository = SolicitacaoRepository()

    def executar(self, tecnico_id):
        return self.solicitacao_repository.buscar_pendentes_com_detalhes(tecnico_id)
