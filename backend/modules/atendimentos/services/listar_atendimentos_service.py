from modules.atendimentos.models.atendimento import Atendimento


class ListarAtendimentosService:
    def executar(self, usuario_id, role):
        return Atendimento.listar_por_usuario(usuario_id, role)
