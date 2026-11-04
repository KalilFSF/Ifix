"""Consultas do módulo servicos: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import services, device_history

class ServicoRepository:
    def buscar_meus_com_participantes(self, usuario_id, como, status=None):
        return services(call_routine("fn_listar_servicos_participante", usuario_id, como, status))

    def buscar_historico_aparelho(self, cliente_id, equipamento, excluir_servico_id=None):
        return device_history(call_routine("fn_historico_aparelho", cliente_id, equipamento, excluir_servico_id)[0])
