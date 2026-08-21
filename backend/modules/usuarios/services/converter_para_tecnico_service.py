from flask import current_app

from exceptions import ValidacaoError
from modules.usuarios.models.tecnico import PerfilTecnico
from utils import salvar_arquivo, validar_dados_tecnico


class ConverterParaTecnicoService:
    """Transforma uma conta cliente já existente em técnico: mesmo id,
    email e senha — só anexa o perfil técnico e troca o papel da conta."""

    def executar(self, usuario, dados_tecnico, foto_perfil, diplomas_arquivos, latitude=None, longitude=None):
        erro = validar_dados_tecnico(dados_tecnico, foto_perfil, diplomas_arquivos)
        if erro:
            raise ValidacaoError(erro)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        nome_foto = salvar_arquivo(foto_perfil, upload_folder + "/perfil")
        nomes_diplomas = [salvar_arquivo(arquivo, upload_folder + "/diplomas") for arquivo in diplomas_arquivos]

        # Atualiza a coordenada mesmo se a conta já tinha uma: a conta pode
        # ser antiga (cadastrada antes da geolocalização existir) ou ter se
        # mudado — e virar técnico é o momento em que a coordenada passa a
        # importar de verdade (ranking automático de chamados).
        if latitude is not None and longitude is not None:
            usuario.latitude = latitude
            usuario.longitude = longitude

        PerfilTecnico.criar(usuario, dados_tecnico, nome_foto, nomes_diplomas)
        return usuario.tornar_tecnico()
