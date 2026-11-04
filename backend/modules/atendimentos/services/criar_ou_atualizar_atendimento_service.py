"""Autoriza o fluxo legado e reaproveita as regras de orçamento em vez de trocar participantes."""
from transactions import atomic,lock_model
from database import db
from exceptions import RecursoNaoEncontradoError,ValidacaoError
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico
from modules.usuarios.models.usuario import Usuario
from modules.atendimentos.models.atendimento import Atendimento
from modules.atendimentos.services.enviar_orcamento_service import EnviarOrcamentoService

class CriarOuAtualizarAtendimentoService:
    @atomic
    def executar(self,dados,servico_id,usuario_id,role):
        usuario = db.session.get(Usuario,usuario_id)
        servico = lock_model(Servico,servico_id)
        if usuario is None or usuario.role != role or servico is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        if any(key in dados for key in ("cliente_id","tecnico_id","servico_id","id")):
            raise ValidacaoError("Participantes não podem ser alterados por esta operação.")
        if dados.get("status","pendente") != "pendente":
            raise ValidacaoError("Use as ações específicas para decidir uma proposta.")
        if servico.status != "aberto" or servico.tecnico_id is not None:
            raise ValidacaoError("Este chamado não recebe mais propostas.")
        if servico.cliente_id==usuario.id:
            if dados.get("valor_orcamento") is not None:
                raise ValidacaoError("O valor de uma proposta deve ser informado pelo técnico convidado.")
            atendimento = Atendimento.query.filter_by(servico_id=servico.id,cliente_id=usuario.id,tecnico_id=None).first()
            limpos = {key:dados[key] for key in ("titulo","descricao") if key in dados}
            return atendimento.atualizar(limpos) if atendimento else Atendimento.criar(limpos,servico.id,usuario.id,"cliente")
        convite = SolicitacaoTecnico.buscar_pendente(servico.id,usuario.id) if usuario.eh_tecnico else None
        if convite is None:
            raise RecursoNaoEncontradoError("Chamado não encontrado.")
        return EnviarOrcamentoService().executar(convite.id,usuario.id,{
            "valor_orcamento":dados.get("valor_orcamento"),"prazo_estimado_dias":dados.get("prazo_estimado_dias"),
            "observacoes":dados.get("descricao") or dados.get("observacoes")})
