from modules.servicos.models.servico import Servico


class CriarServicoService:
    def executar(self, dados, cliente_id):
        return Servico.criar(dados, cliente_id)
