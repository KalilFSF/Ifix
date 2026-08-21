from exceptions import ValidacaoError
from modules.usuarios.models.usuario import Usuario
from utils import validar_campos_comuns


class CadastrarClienteService:
    def executar(self, dados, senha, confirmar_senha):
        erro = validar_campos_comuns(dados, senha, confirmar_senha)
        if erro:
            raise ValidacaoError(erro)

        if Usuario.buscar_por_cpf(dados["cpf"]) is not None:
            raise ValidacaoError("Já existe uma conta com este CPF.")
        if Usuario.buscar_por_email(dados["email"]) is not None:
            raise ValidacaoError("Já existe uma conta com este email.")

        return Usuario.criar(dados, senha, "cliente")
