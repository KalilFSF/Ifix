from models import Usuario


class AuthService:
    @staticmethod
    def autenticar(email, senha):
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario is None or not usuario.check_senha(senha):
            return None
        return usuario
