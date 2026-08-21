from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError
from modules.atendimentos.models.avaliacao import Avaliacao
from modules.servicos.models.servico import Servico


class ListarAvaliacoesService:
    def executar(self, servico_id, usuario):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if usuario.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        return Avaliacao.listar_por_servico(servico_id)
