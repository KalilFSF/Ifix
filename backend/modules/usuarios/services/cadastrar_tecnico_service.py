from flask import current_app

from exceptions import ContaClienteExistenteError, ValidacaoError
from modules.usuarios.models.tecnico import PerfilTecnico
from modules.usuarios.models.usuario import Usuario
from utils import salvar_arquivo, validar_campos_comuns, validar_dados_tecnico


class CadastrarTecnicoService:
    def executar(self, dados, dados_tecnico, senha, confirmar_senha, foto_perfil, diplomas_arquivos):
        # Email já é de uma conta cliente: não é duplicidade comum, é alguém
        # que já tem conta e quer virar técnico — a conversão exige provar
        # dono fazendo login, então aqui só sinalizamos a situação.
        conta_existente = Usuario.buscar_por_email(dados["email"])
        if conta_existente is not None and conta_existente.role == "cliente":
            raise ContaClienteExistenteError(
                "Este email já tem uma conta de cliente. Faça login e converta sua conta em técnico pela área do cliente."
            )

        erro = validar_campos_comuns(dados, senha, confirmar_senha)
        if not erro:
            erro = validar_dados_tecnico(dados_tecnico, foto_perfil, diplomas_arquivos)
        if erro:
            raise ValidacaoError(erro)

        if Usuario.buscar_por_cpf(dados["cpf"]) is not None:
            raise ValidacaoError("Já existe uma conta com este CPF.")
        if conta_existente is not None:
            raise ValidacaoError("Já existe uma conta com este email.")

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        nome_foto = salvar_arquivo(foto_perfil, upload_folder + "/perfil")
        nomes_diplomas = [salvar_arquivo(arquivo, upload_folder + "/diplomas") for arquivo in diplomas_arquivos]

        usuario = Usuario.criar(dados, senha, "tecnico")
        PerfilTecnico.criar(usuario, dados_tecnico, nome_foto, nomes_diplomas)
        return usuario
