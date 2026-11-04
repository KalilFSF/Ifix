"""Autoriza escolha/recusa de proposta legada sem alterar indevidamente o responsável."""
from transactions import atomic,lock_child
from exceptions import RecursoNaoEncontradoError,ValidacaoError
from modules.atendimentos.models.atendimento import Atendimento
from modules.atendimentos.services.escolher_orcamento_service import EscolherOrcamentoService

class AtualizarStatusAtendimentoService:
    @atomic
    def executar(self,atendimento_id,dados,usuario):
        atendimento = lock_child(Atendimento,atendimento_id)
        if atendimento is None or usuario.id not in (atendimento.cliente_id,atendimento.tecnico_id):
            raise RecursoNaoEncontradoError("Atendimento não encontrado.")
        if set(dados) != {"status"}:
            raise ValidacaoError("Esta operação altera apenas o status da proposta.")
        status = dados["status"]
        if status=="aceito":
            if usuario.id != atendimento.cliente_id:
                raise RecursoNaoEncontradoError("Atendimento não encontrado.")
            EscolherOrcamentoService().executar(atendimento.id,usuario)
            return atendimento
        if atendimento.status != "pendente" or atendimento.servico.status != "aberto":
            raise ValidacaoError("Esta proposta já foi decidida ou o chamado encerrado.")
        if status != "recusado":
            raise ValidacaoError("Transição inválida de status da proposta.")
        atendimento.marcar_recusado()
        from modules.servicos.models.solicitacao import SolicitacaoTecnico
        convite = SolicitacaoTecnico.buscar_por_servico_e_tecnico(atendimento.servico_id,atendimento.tecnico_id)
        if convite:
            convite.marcar_recusada()
        return atendimento
