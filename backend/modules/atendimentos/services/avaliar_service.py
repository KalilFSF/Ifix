from constants import STATUS_FINALIZADO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.atendimentos.models.avaliacao import Avaliacao
from modules.servicos.models.servico import Servico
from modules.usuarios.models.tecnico import PerfilTecnico


class AvaliarService:
    """Avaliação mútua pós-chamado: cliente avalia o técnico e vice-versa,
    uma vez cada, só depois do chamado finalizado. Quando o avaliado é o
    técnico, alimenta PerfilTecnico.nota_media (via registrar_avaliacao),
    o critério de avaliação usado por SelecionarTecnicosService."""

    def executar(self, servico_id, autor, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.status != STATUS_FINALIZADO:
            raise ValidacaoError("Só é possível avaliar um chamado finalizado.")
        if autor.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        avaliado_id = servico.tecnico_id if autor.id == servico.cliente_id else servico.cliente_id
        if avaliado_id is None:
            raise ValidacaoError("Chamado sem técnico atribuído.")

        if Avaliacao.buscar_por_servico_e_autor(servico_id, autor.id):
            raise ValidacaoError("Você já avaliou este chamado.")

        nota = self._parse_nota(dados.get("nota"))
        comentario = (dados.get("comentario") or "").strip()

        avaliacao = Avaliacao.criar(servico_id, autor.id, avaliado_id, nota, comentario)

        if avaliado_id == servico.tecnico_id:
            perfil = PerfilTecnico.buscar_por_usuario_id(avaliado_id)
            if perfil:
                perfil.registrar_avaliacao(nota)

        return avaliacao

    @staticmethod
    def _parse_nota(valor):
        try:
            nota = int(valor)
        except (TypeError, ValueError):
            raise ValidacaoError("Informe uma nota válida (1 a 5).")
        if nota < 1 or nota > 5:
            raise ValidacaoError("A nota deve ser entre 1 e 5.")
        return nota
