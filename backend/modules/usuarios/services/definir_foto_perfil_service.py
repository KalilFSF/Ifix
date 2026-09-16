from flask import current_app

from exceptions import ValidacaoError
from utils import IMAGE_EXTENSIONS, extensao_permitida, salvar_arquivo

MAX_BYTES_FOTO_PERFIL = 5 * 1024 * 1024


class DefinirFotoPerfilService:
    """Troca a foto de perfil de qualquer conta (cliente ou técnico).

    Grava em Usuario.foto_perfil e não em PerfilTecnico.foto_perfil: aquela
    coluna é NOT NULL e nasce no cadastro do técnico, então continua sendo o
    valor original. A de Usuario é a que a interface exibe, com fallback
    para a do perfil técnico em Usuario.to_dict().
    """

    def executar(self, usuario, arquivo):
        if arquivo is None or not arquivo.filename:
            raise ValidacaoError("Escolha uma imagem para enviar.")
        if not extensao_permitida(arquivo.filename, IMAGE_EXTENSIONS):
            raise ValidacaoError("A foto deve ser png, jpg, jpeg ou webp.")

        posicao = arquivo.stream.tell()
        arquivo.stream.seek(0, 2)
        tamanho = arquivo.stream.tell()
        arquivo.stream.seek(posicao)
        if tamanho > MAX_BYTES_FOTO_PERFIL:
            raise ValidacaoError(
                f"A foto deve ter no máximo {MAX_BYTES_FOTO_PERFIL // (1024 * 1024)} MB."
            )

        pasta = current_app.config["UPLOAD_FOLDER"] + "/perfil"
        url = salvar_arquivo(arquivo, pasta)
        return usuario.definir_foto_perfil(url)
