from constants import CATEGORIAS_PROBLEMA, MODALIDADES
from exceptions import ValidacaoError
from modules.usuarios.repositories.usuario_repository import UsuarioRepository

ORDENS_VALIDAS = ("nota", "atendimentos")
MAX_CARACTERES_BUSCA = 60


class ListarDiretorioTecnicosService:
    """Diretório de técnicos (funcionalidade 4). Cada filtro é opcional; o
    que sai daqui é só o que a procedure fn_listar_tecnicos_diretorio expõe
    de propósito — sem e-mail, telefone, CPF nem coordenadas."""

    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    def executar(self, filtros):
        return self.usuario_repository.listar_diretorio_tecnicos(
            busca=self._parse_busca(filtros.get("busca")),
            categoria=self._parse_opcao(filtros.get("categoria"), CATEGORIAS_PROBLEMA, "categoria"),
            modalidade=self._parse_opcao(filtros.get("modalidade"), MODALIDADES, "modalidade"),
            nota_minima=self._parse_nota_minima(filtros.get("nota_minima")),
            disponivel=self._parse_bool(filtros.get("disponivel")),
            ordem=self._parse_opcao(filtros.get("ordem"), ORDENS_VALIDAS, "ordem") or "nota",
        )

    @staticmethod
    def _parse_busca(valor):
        busca = (valor or "").strip()[:MAX_CARACTERES_BUSCA]
        return busca or None

    @staticmethod
    def _parse_opcao(valor, validas, nome):
        opcao = (valor or "").strip().lower()
        if not opcao:
            return None
        if opcao not in validas:
            raise ValidacaoError(f"Filtro de {nome} inválido.")
        return opcao

    @staticmethod
    def _parse_nota_minima(valor):
        if valor in (None, ""):
            return None
        try:
            nota = float(valor)
        except (TypeError, ValueError):
            raise ValidacaoError("Nota mínima inválida.") from None
        if not 0 <= nota <= 5:
            raise ValidacaoError("A nota mínima deve estar entre 0 e 5.")
        return nota

    @staticmethod
    def _parse_bool(valor):
        return str(valor or "").strip().lower() in {"1", "true", "sim", "on"}
