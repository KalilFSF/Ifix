"""Consultas do módulo atendimentos: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import project, REVIEW_FIELDS

class AvaliacaoRepository:
    def listar_por_servico(self, servico_id):
        return [project(row, REVIEW_FIELDS) for row in call_routine("fn_listar_avaliacoes_por_servico", servico_id)[0]]
