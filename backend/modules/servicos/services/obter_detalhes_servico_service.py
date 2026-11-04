"""Autoriza o chamado e escolhe a projeção completa ou reduzida conforme a participação."""
from access import service_access,invited_payload
from serialization import to_jsonable

class ObterDetalhesServicoService:
    def executar(self,servico_id,usuario):
        servico,invited = service_access(servico_id,usuario,allow_invited=True)
        if invited:
            # Fotos do problema são necessárias ao orçamento; demais dados privados ficam restritos.
            from constants import URGENCIA_TAXA_PERCENTUAL,MODALIDADES_LABELS
            fields = "id codigo titulo descricao categoria tipo_equipamento equipamento preco_estimado valor_maximo_aprovado garantia urgente modalidade status criado_em atualizado_em"
            payload = {field:getattr(servico,field) for field in fields.split()}
            payload["urgencia_taxa_percentual"] = URGENCIA_TAXA_PERCENTUAL if servico.urgente else None
            payload["modalidade_label"] = MODALIDADES_LABELS.get(servico.modalidade)
            payload["fotos"] = [foto.to_dict() for foto in servico.fotos]
            return to_jsonable(invited_payload(payload))
        payload = servico.to_dict()
        allowed = servico.atendimentos if servico.cliente_id==usuario.id else [a for a in servico.atendimentos if a.tecnico_id==usuario.id]
        payload["atendimentos"] = [a.to_dict() for a in allowed]
        return payload
