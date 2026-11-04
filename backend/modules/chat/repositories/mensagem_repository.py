"""Consultas do módulo chat: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import project

class MensagemRepository:
    def listar_por_servico(self, servico_id, desde_id=None):
        return [project(row,"id servico_id autor_id autor_nome autor_foto conteudo lida_em criado_em") for row in call_routine("fn_listar_mensagens_chamado", servico_id, desde_id)[0]]

    def contar_nao_lidas_por_servico(self, usuario_id):
        return {row["servico_id"]: int(row["nao_lidas"]) for row in call_routine("fn_contar_mensagens_nao_lidas", usuario_id)[0]}
