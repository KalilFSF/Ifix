from exceptions import ValidacaoError
from modules.usuarios.models.usuario import Usuario
from utils import parsear_coordenada, somente_digitos


class AtualizarUsuarioService:
    """Atualização dos dados da própria conta (PATCH /api/me), usada pela
    tela de perfil.

    A validação mora aqui, e não na Model, porque `Usuario.atualizar` é um
    setter burro: sem isto, um nome vazio ou uma latitude com texto entrava
    no banco sem reclamar.
    """

    CAMPOS_TEXTO = ("nome", "telefone", "cep", "estado", "cidade", "bairro", "endereco", "numero", "complemento")

    def executar(self, usuario, dados):
        limpos = {}

        for campo in self.CAMPOS_TEXTO:
            if campo in dados:
                limpos[campo] = (dados.get(campo) or "").strip() or None

        if "nome" in limpos and (not limpos["nome"] or len(limpos["nome"]) < 3):
            raise ValidacaoError("Informe seu nome completo.")
        if "telefone" in limpos and not limpos["telefone"]:
            raise ValidacaoError("Informe um telefone válido.")

        if "cep" in limpos and limpos["cep"]:
            cep = somente_digitos(limpos["cep"])
            if len(cep) != 8:
                raise ValidacaoError("Informe um CEP válido (8 dígitos).")
            limpos["cep"] = cep

        if "estado" in limpos and limpos["estado"]:
            limpos["estado"] = limpos["estado"].upper()[:2]

        # Coordenadas só entram se forem parseáveis: mandar texto inválido
        # não pode apagar a localização já cadastrada, senão o técnico sairia
        # do ranking (fn_listar_tecnicos_para_ranking exige lat/long) por um
        # erro de digitação em outro campo do mesmo formulário.
        for campo in ("latitude", "longitude"):
            if campo in dados:
                valor = parsear_coordenada(dados.get(campo))
                if valor is not None:
                    limpos[campo] = valor

        # Antes do "nada para atualizar": quem manda só o e-mail merece saber
        # por que ele não mudou, e não uma mensagem genérica.
        if "email" in dados and (dados.get("email") or "").strip().lower() != (usuario.email or "").lower():
            raise ValidacaoError(
                "O e-mail não pode ser alterado por aqui — ele identifica a conta no login."
            )

        if not limpos:
            raise ValidacaoError("Nada para atualizar.")

        return usuario.atualizar(limpos)
