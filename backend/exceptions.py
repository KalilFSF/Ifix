# Exceções de domínio levantadas pelas Services e traduzidas pelos
# Controllers em jsonify(...), status_code — nenhum Controller precisa de
# um if/elif por tipo de erro, só "except DominioError as erro".

class DominioError(Exception):
    status_code = 400

    def __init__(self, mensagem, **extra):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.extra = extra


class ValidacaoError(DominioError):
    status_code = 400


class RecursoNaoEncontradoError(DominioError):
    status_code = 404


class PermissaoNegadaError(DominioError):
    status_code = 403


class ContaClienteExistenteError(DominioError):
    status_code = 409

    def __init__(self, mensagem):
        super().__init__(mensagem, conta_existente="cliente")


class SolicitacaoJaRespondidaError(DominioError):
    status_code = 409


class CredenciaisInvalidasError(DominioError):
    status_code = 401
