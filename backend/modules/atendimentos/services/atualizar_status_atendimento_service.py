from exceptions import RecursoNaoEncontradoError
from modules.atendimentos.models.atendimento import Atendimento


class AtualizarStatusAtendimentoService:
    def executar(self, atendimento_id, dados, tecnico_id):
        atendimento = Atendimento.buscar_por_id(atendimento_id)
        if atendimento is None:
            raise RecursoNaoEncontradoError("Atendimento não encontrado.")

        atendimento.atualizar(dados)
        return atendimento.definir_responsavel(tecnico_id, "tecnico")
