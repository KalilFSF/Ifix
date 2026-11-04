"""Consultas do módulo servicos: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import project, APPROVAL_FIELDS

class AprovacaoRepository:
    def listar_por_servico(self, servico_id):
        return [project(row, APPROVAL_FIELDS) for row in call_routine("fn_listar_aprovacoes_por_servico", servico_id)[0]]
