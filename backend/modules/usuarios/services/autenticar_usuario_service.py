from exceptions import CredenciaisInvalidasError
from modules.usuarios.models.usuario import Usuario


class AutenticarUsuarioService:
    def executar(self, email, senha):
        usuario = Usuario.buscar_por_email(email)
        if usuario is None or not usuario.check_senha(senha):
            raise CredenciaisInvalidasError("Email ou senha inválidos.")
        return usuario
