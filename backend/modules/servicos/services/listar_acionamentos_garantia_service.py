from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.servicos.models.garantia import AcionamentoGarantia
from modules.servicos.models.servico import Servico


class ListarAcionamentosGarantiaService:
    """Acionamentos de garantia de um chamado, para os dois lados: o cliente
    acompanha o que pediu, o técnico vê o que precisa resolver."""

    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if usuario.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        return AcionamentoGarantia.listar_por_servico(servico_id)
