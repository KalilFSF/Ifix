from modules.servicos.repositories.servico_repository import ServicoRepository


class ListarMeusServicosService:
    def __init__(self):
        self.servico_repository = ServicoRepository()

    def executar(self, usuario_id, role, status=None):
        return self.servico_repository.buscar_meus_com_participantes(usuario_id, role, status)
