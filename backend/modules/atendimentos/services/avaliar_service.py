"""Registra avaliação única pós-conclusão e atualiza médias ou alertas do participante avaliado."""
from transactions import atomic, lock_model, lock_child
from sqlalchemy.exc import IntegrityError

from constants import NOTA_COMPORTAMENTO_LIMITE, STATUS_FINALIZADO
from database import db
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

    @atomic
    def executar(self, servico_id, autor, dados):
        servico = lock_model(Servico, servico_id)
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

        # Adquirir locks antes do INSERT: FKs InnoDB tomam locks compartilhados.
        # Ordem estável evita upgrade simultâneo desses locks em avaliações cruzadas.
        for user_id in sorted({servico.cliente_id,servico.tecnico_id}):
            lock_model(Usuario,user_id)

        if Avaliacao.buscar_por_servico_e_autor(servico_id, autor.id):
            raise ValidacaoError("Você já avaliou este chamado.")

        comentario = (dados.get("comentario") or "").strip()

        # Lock do chamado serializa avaliações; UNIQUE é a segunda barreira.
        if autor_e_tecnico:
            return self._avaliar_cliente(servico_id, autor.id, avaliado_id, dados, comentario)
        return self._avaliar_tecnico(servico_id, autor.id, avaliado_id, dados, comentario)

    def _avaliar_tecnico(self, servico_id, autor_id, tecnico_id, dados, comentario):
        nota_tempo = self._parse_nota(dados.get("nota_tempo"), "tempo de atendimento")
        nota_honestidade = self._parse_nota(dados.get("nota_honestidade"), "honestidade")
        nota_preco_justo = self._parse_nota(dados.get("nota_preco_justo"), "preço justo")
        nota_geral = round((nota_tempo + nota_honestidade + nota_preco_justo) / 3)

        avaliacao = Avaliacao.criar(
            servico_id, autor_id, tecnico_id, nota_geral, comentario,
            nota_tempo=nota_tempo, nota_honestidade=nota_honestidade, nota_preco_justo=nota_preco_justo,
        )

        lock_model(Usuario, tecnico_id)
        from sqlalchemy import select
        perfil = db.session.execute(select(PerfilTecnico).where(PerfilTecnico.usuario_id==tecnico_id)
            .with_for_update().execution_options(populate_existing=True)).scalar_one_or_none()
        if perfil:
            perfil.registrar_avaliacao(nota_geral)
        else:
            # Usuario.eh_tecnico aceita role="tecnico" SEM perfis_tecnicos, e
            # nesse caso a nota não tem onde ser acumulada. A avaliação fica
            # gravada, mas o técnico não entra no ranking (a procedure
            # fn_listar_tecnicos_para_ranking faz JOIN com perfis_tecnicos) —
            # o que é um problema de cadastro, não de avaliação.
            print(f"[avaliacao] técnico {tecnico_id} não tem perfil técnico; nota_media não atualizada.")

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
            cliente = lock_model(Usuario, cliente_id)
            if cliente:
                cliente.registrar_alerta_comportamento()

        return avaliacao

    @staticmethod
    def _parse_nota(valor, nome_criterio):
        try:
            nota = int(valor)
        except (TypeError, ValueError):
            raise ValidacaoError(f"Informe uma nota válida para {nome_criterio} (1 a 5).") from None
        if nota < 1 or nota > 5:
            raise ValidacaoError(f"A nota de {nome_criterio} deve ser entre 1 e 5.")
        return nota
