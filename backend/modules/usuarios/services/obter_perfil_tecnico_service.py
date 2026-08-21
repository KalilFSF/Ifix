from exceptions import RecursoNaoEncontradoError


class ObterPerfilTecnicoService:
    def executar(self, usuario):
        perfil = usuario.perfil_tecnico
        if not perfil:
            raise RecursoNaoEncontradoError("Perfil não encontrado.")
        return perfil
