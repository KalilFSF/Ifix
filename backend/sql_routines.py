"""CALL na conexão da sessão, com parâmetros e drenagem de todos os resultados."""
from database import db

ROUTINES = frozenset({
    "fn_listar_tecnicos_com_perfil", "fn_listar_tecnicos_para_ranking",
    "fn_listar_tecnicos_diretorio", "fn_perfil_publico_tecnico",
    "fn_listar_servicos_participante", "fn_historico_aparelho",
    "fn_listar_solicitacoes_pendentes", "fn_listar_orcamentos_por_servico",
    "fn_listar_aprovacoes_por_servico", "fn_listar_mensagens_chamado",
    "fn_contar_mensagens_nao_lidas", "fn_listar_avaliacoes_por_servico",
})

def call_routine(name, *params):
    """Executa uma procedure permitida e retorna uma lista de conjuntos de linhas.

    Usa a conexão da transação atual: fecha somente o cursor e não faz commit.
    Valores são parâmetros; apenas o nome previamente autorizado entra no SQL.
    """
    if name not in ROUTINES:
        raise ValueError("Rotina não autorizada.")
    db.session.flush()
    dbapi_connection = db.session.connection().connection.driver_connection
    cursor = dbapi_connection.cursor()
    result_sets = []
    try:
        placeholders = ", ".join(["%s"] * len(params))
        cursor.execute(f"CALL {name}({placeholders})", params)
        while True:
            if cursor.description is not None:
                column_names = [column[0] for column in cursor.description]
                result_sets.append([dict(zip(column_names, row)) for row in cursor.fetchall()])
            if not cursor.nextset():
                break
    finally:
        cursor.close()
    return result_sets
