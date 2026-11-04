"""Mantém o endpoint legado de listagem usando a projeção pública do diretório."""
from modules.usuarios.repositories.usuario_repository import UsuarioRepository


class ListarTecnicosService:
    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    def executar(self):
        return self.usuario_repository.buscar_tecnicos_com_perfil()
