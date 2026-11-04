"""Autorização por recurso e recorte de convites antes da serialização."""
from exceptions import RecursoNaoEncontradoError
from modules.servicos.models.servico import Servico
from modules.servicos.models.solicitacao import SolicitacaoTecnico

INVITED_FIELDS = "id codigo titulo descricao categoria tipo_equipamento equipamento preco_estimado valor_maximo_aprovado garantia urgente urgencia_taxa_percentual modalidade modalidade_label status criado_em atualizado_em fotos"

def service_access(servico_id,user,allow_invited=False):
    servico = Servico.buscar_por_id(servico_id)
    if servico is None:
        raise RecursoNaoEncontradoError("Chamado não encontrado.")
    if user.id in (servico.cliente_id,servico.tecnico_id):
        return servico,False
    if allow_invited and user.eh_tecnico and servico.status=="aberto" and servico.tecnico_id is None:
        convite = SolicitacaoTecnico.buscar_por_servico_e_tecnico(servico.id,user.id)
        if convite and convite.status in {"pendente","orcamento_enviado","aceita"}:
            return servico,True
    # Mesmo erro de um ID inexistente, sem confirmar a existência de terceiros.
    raise RecursoNaoEncontradoError("Chamado não encontrado.")


def invited_payload(source):
    return {key:source.get(key) for key in INVITED_FIELDS.split()}
