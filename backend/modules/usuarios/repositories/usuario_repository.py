"""Consultas do módulo usuarios: chama rotinas MySQL parametrizadas e aplica projeções explícitas."""
from sql_routines import call_routine
from query_serializers import directory, public_profile, project

class UsuarioRepository:
    def buscar_tecnicos_com_perfil(self):
        return self.listar_diretorio_tecnicos()

    def buscar_tecnicos_para_ranking(self):
        rows = call_routine("fn_listar_tecnicos_para_ranking")[0]
        for row in rows:
            row["disponivel_agora"] = bool(row["disponivel_agora"])
        return rows

    def listar_diretorio_tecnicos(self, busca=None, categoria=None, modalidade=None,
                                  nota_minima=None, disponivel=False, ordem="nota"):
        return [directory(row) for row in call_routine("fn_listar_tecnicos_diretorio", busca, categoria, modalidade, nota_minima, disponivel, ordem)[0]]

    def obter_perfil_publico_tecnico(self, usuario_id):
        return public_profile(call_routine("fn_perfil_publico_tecnico", usuario_id))
