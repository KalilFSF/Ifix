from exceptions import RecursoNaoEncontradoError


class AtualizarPerfilTecnicoService:
    def executar(self, usuario, dados):
        perfil = usuario.perfil_tecnico
        if not perfil:
            raise RecursoNaoEncontradoError("Perfil não encontrado.")
        return perfil.atualizar(dados)
