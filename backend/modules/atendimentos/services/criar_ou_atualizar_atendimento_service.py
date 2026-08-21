from modules.atendimentos.models.atendimento import Atendimento


class CriarOuAtualizarAtendimentoService:
    def executar(self, dados, servico_id, usuario_id, role):
        atendimento = Atendimento.buscar_por_servico(servico_id)
        if atendimento is None:
            return Atendimento.criar(dados, servico_id, usuario_id, role)

        atendimento.atualizar(dados)
        return atendimento.definir_responsavel(usuario_id, role)
