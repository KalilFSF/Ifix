"""Consultas do módulo servicos: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import requests

class SolicitacaoRepository:
    def buscar_pendentes_com_detalhes(self, tecnico_id):
        return requests(call_routine("fn_listar_solicitacoes_pendentes", tecnico_id))
