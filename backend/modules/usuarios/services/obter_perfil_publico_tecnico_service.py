from exceptions import RecursoNaoEncontradoError
from modules.usuarios.repositories.usuario_repository import UsuarioRepository


class ObterPerfilPublicoTecnicoService:
    """Perfil público do técnico (funcionalidade 5): o que um cliente pode
    ver antes de escolher. O recorte de dados é feito na procedure
    fn_perfil_publico_tecnico — contato e localização exata não saem."""

    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    def executar(self, tecnico_id):
        perfil = self.usuario_repository.obter_perfil_publico_tecnico(tecnico_id)
        if perfil is None:
            raise RecursoNaoEncontradoError("Técnico não encontrado.")
        return perfil
