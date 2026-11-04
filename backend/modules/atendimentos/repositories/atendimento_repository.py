"""Consultas do módulo atendimentos: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import budgets

class AtendimentoRepository:
    def listar_por_servico_com_tecnico(self, servico_id):
        return budgets(call_routine("fn_listar_orcamentos_por_servico", servico_id)[0])
