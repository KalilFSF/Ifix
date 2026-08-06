from database import db
from models import Usuario


class UsuarioService:
    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_cpf(cpf):
        return Usuario.query.filter_by(cpf=cpf).first()

    @staticmethod
    def listar_tecnicos():
        return Usuario.query.filter_by(role="tecnico").all()

    @staticmethod
    def listar_clientes():
        return Usuario.query.filter_by(role="cliente").all()

    @staticmethod
    def atualizar_usuario(usuario, dados):
        if "nome" in dados:
            usuario.nome = dados["nome"]
        if "telefone" in dados:
            usuario.telefone = dados["telefone"]
        if "cidade" in dados:
            usuario.cidade = dados["cidade"]
        if "estado" in dados:
            usuario.estado = dados["estado"]
        if "endereco" in dados:
            usuario.endereco = dados["endereco"]
        db.session.commit()
        return usuario
