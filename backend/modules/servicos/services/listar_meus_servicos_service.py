from modules.servicos.repositories.servico_repository import ServicoRepository


class ListarMeusServicosService:
    def __init__(self):
        self.servico_repository = ServicoRepository()

    def executar(self, usuario_id, como, status=None):
        """como: 'cliente' lista chamados abertos pelo usuário;
        'tecnico' lista chamados que ele atende."""
        return self.servico_repository.buscar_meus_com_participantes(usuario_id, como, status)
