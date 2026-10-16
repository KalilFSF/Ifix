from constants import MODALIDADES
from exceptions import RecursoNaoEncontradoError, ValidacaoError
from utils import ESCOLARIDADES_VALIDAS

CAMPOS_TEXTO = (
    "especialidade", "escolaridade", "curso_superior",
    "regiao_atendimento", "cursos_experiencias", "especializacoes",
)

OBRIGATORIOS = ("especialidade", "escolaridade", "regiao_atendimento")


class AtualizarPerfilTecnicoService:
    """Edição dos dados profissionais pela tela de perfil.

    Valida aqui o que o cadastro já validava em utils.validar_dados_tecnico:
    sem isso a edição poderia esvaziar campos que são NOT NULL na Model, ou
    gravar uma escolaridade fora do catálogo aceito no cadastro.
    """

    def executar(self, usuario, dados):
        perfil = usuario.perfil_tecnico
        if not perfil:
            raise RecursoNaoEncontradoError("Perfil não encontrado.")

        limpos = {}
        for campo in CAMPOS_TEXTO:
            if campo in dados:
                limpos[campo] = (dados.get(campo) or "").strip() or None

        for campo in OBRIGATORIOS:
            if campo in limpos and not limpos[campo]:
                raise ValidacaoError(f"O campo {campo.replace('_', ' ')} é obrigatório.")

        if limpos.get("escolaridade") and limpos["escolaridade"] not in ESCOLARIDADES_VALIDAS:
            raise ValidacaoError("Selecione uma escolaridade válida.")

        if "valor_medio" in dados:
            limpos["valor_medio"] = self._parse_valor_medio(dados.get("valor_medio"))

        if "modalidades" in dados:
            limpos["modalidades"] = self._parse_modalidades(dados.get("modalidades"))

        if not limpos:
            raise ValidacaoError("Nada para atualizar.")

        return perfil.atualizar(limpos)

    @staticmethod
    def _parse_modalidades(valor):
        """Lista fechada (constants.MODALIDADES). Vazia não vale: o técnico
        sem nenhuma modalidade não receberia chamado nenhum — pra não
        escolher, é só não mexer (nulo = atende todas)."""
        if not isinstance(valor, (list, tuple)):
            raise ValidacaoError("Informe as modalidades de atendimento em uma lista.")
        escolhidas = []
        for item in valor:
            modalidade = str(item or "").strip().lower()
            if modalidade not in MODALIDADES:
                raise ValidacaoError("Modalidade de atendimento inválida.")
            if modalidade not in escolhidas:
                escolhidas.append(modalidade)
        if not escolhidas:
            raise ValidacaoError("Selecione ao menos uma modalidade de atendimento.")
        return ",".join(m for m in MODALIDADES if m in escolhidas)

    @staticmethod
    def _parse_valor_medio(valor):
        """Nulo/vazio é válido: significa "não informo preço médio", e o
        ranking trata isso como neutro (score 0.5 em SelecionarTecnicosService)
        em vez de penalizar."""
        if valor in (None, ""):
            return None
        try:
            numero = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValidacaoError("Informe um valor médio válido.") from None
        if numero < 0:
            raise ValidacaoError("O valor médio não pode ser negativo.")
        return round(numero, 2)
