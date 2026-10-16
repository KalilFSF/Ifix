from modules.usuarios.models.disponibilidade import JanelaDisponibilidade


class ObterDisponibilidadeService:
    """Janelas semanais e status "disponível agora" do técnico logado."""

    def executar(self, tecnico):
        perfil = tecnico.perfil_tecnico
        return {
            "janelas": [janela.to_dict() for janela in JanelaDisponibilidade.listar_por_tecnico(tecnico.id)],
            "disponivel_agora": bool(perfil and perfil.disponivel_agora),
        }
