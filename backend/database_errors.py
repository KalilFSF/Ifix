"""Diagnóstico MySQL com campos fixos, sem mensagens/SQL/credenciais."""
import ssl

CATEGORIES = {
    1044: "permissao_banco",
    1045: "autenticacao",
    1049: "banco_inexistente",
    1054: "coluna_inexistente",
    1064: "sintaxe_sql",
    1129: "host_bloqueado",
    1130: "host_nao_autorizado",
    1142: "permissao_operacao",
    1146: "tabela_inexistente",
    1205: "timeout_lock",
    1213: "deadlock",
    1305: "rotina_inexistente",
    2002: "conexao",
    2003: "conexao",
    2006: "conexao_encerrada",
    2013: "conexao_perdida",
    2026: "tls",
}


def mysql_error_info(error):
    original = getattr(error,"orig",error)
    arguments = getattr(original,"args",())
    code = arguments[0] if arguments and type(arguments[0]) is int else None
    category = CATEGORIES.get(code,"banco_nao_classificado")
    current = original
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current,ssl.SSLCertVerificationError):
            category = "certificado_tls"
            break
        if isinstance(current,ssl.SSLError):
            category = "tls"
            break
        current = current.__cause__ or current.__context__
    return code,category
