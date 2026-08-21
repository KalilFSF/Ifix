from constants import NOTA_COMPORTAMENTO_LIMITE, STATUS_FINALIZADO
from exceptions import PermissaoNegadaError, RecursoNaoEncontradoError, ValidacaoError
from modules.atendimentos.models.avaliacao import Avaliacao
from modules.servicos.models.servico import Servico
from modules.usuarios.models.tecnico import PerfilTecnico
from modules.usuarios.models.usuario import Usuario


class AvaliarService:
    """Avaliação mútua pós-chamado, uma vez cada, só depois do chamado
    finalizado — mas com critérios diferentes por direção, porque avaliar
    o SERVIÇO do técnico e avaliar o COMPORTAMENTO do cliente são coisas
    diferentes:
    - Cliente avalia o técnico: tempo de atendimento, honestidade, preço
      justo. Alimenta PerfilTecnico.nota_media (via registrar_avaliacao),
      o critério de avaliação usado por SelecionarTecnicosService.
    - Técnico avalia o cliente: comportamento, colaboração/não
      interferência no atendimento. Nota baixa nesses critérios gera um
      alerta de comportamento (ver Usuario.registrar_alerta_comportamento)
      que, acumulado, suspende a conta do cliente."""

    def executar(self, servico_id, autor, dados):
        servico = Servico.buscar_por_id(servico_id)
        if servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if servico.status != STATUS_FINALIZADO:
            raise ValidacaoError("Só é possível avaliar um chamado finalizado.")
        if autor.id not in (servico.cliente_id, servico.tecnico_id):
            raise PermissaoNegadaError("Acesso negado.")

        autor_e_tecnico = autor.id == servico.tecnico_id
        avaliado_id = servico.cliente_id if autor_e_tecnico else servico.tecnico_id
        if avaliado_id is None:
            raise ValidacaoError("Chamado sem técnico atribuído.")

        if Avaliacao.buscar_por_servico_e_autor(servico_id, autor.id):
            raise ValidacaoError("Você já avaliou este chamado.")

        comentario = (dados.get("comentario") or "").strip()

        if autor_e_tecnico:
            avaliacao = self._avaliar_cliente(servico_id, autor.id, avaliado_id, dados, comentario)
        else:
            avaliacao = self._avaliar_tecnico(servico_id, autor.id, avaliado_id, dados, comentario)

        return avaliacao

    def _avaliar_tecnico(self, servico_id, autor_id, tecnico_id, dados, comentario):
        nota_tempo = self._parse_nota(dados.get("nota_tempo"), "tempo de atendimento")
        nota_honestidade = self._parse_nota(dados.get("nota_honestidade"), "honestidade")
        nota_preco_justo = self._parse_nota(dados.get("nota_preco_justo"), "preço justo")
        nota_geral = round((nota_tempo + nota_honestidade + nota_preco_justo) / 3)

        avaliacao = Avaliacao.criar(
            servico_id, autor_id, tecnico_id, nota_geral, comentario,
            nota_tempo=nota_tempo, nota_honestidade=nota_honestidade, nota_preco_justo=nota_preco_justo,
        )

        perfil = PerfilTecnico.buscar_por_usuario_id(tecnico_id)
        if perfil:
            perfil.registrar_avaliacao(nota_geral)

        return avaliacao

    def _avaliar_cliente(self, servico_id, autor_id, cliente_id, dados, comentario):
        nota_comportamento = self._parse_nota(dados.get("nota_comportamento"), "comportamento")
        nota_colaboracao = self._parse_nota(dados.get("nota_colaboracao"), "colaboração durante o atendimento")
        nota_geral = round((nota_comportamento + nota_colaboracao) / 2)

        avaliacao = Avaliacao.criar(
            servico_id, autor_id, cliente_id, nota_geral, comentario,
            nota_comportamento=nota_comportamento, nota_colaboracao=nota_colaboracao,
        )

        if min(nota_comportamento, nota_colaboracao) <= NOTA_COMPORTAMENTO_LIMITE:
            cliente = Usuario.buscar_por_id(cliente_id)
            if cliente:
                cliente.registrar_alerta_comportamento()

        return avaliacao

    @staticmethod
    def _parse_nota(valor, nome_criterio):
        try:
            nota = int(valor)
        except (TypeError, ValueError):
            raise ValidacaoError(f"Informe uma nota válida para {nome_criterio} (1 a 5).")
        if nota < 1 or nota > 5:
            raise ValidacaoError(f"A nota de {nome_criterio} deve ser entre 1 e 5.")
        return nota
