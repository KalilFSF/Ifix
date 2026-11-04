"""Inicialização MANUAL e não destrutiva. Importar este módulo não conecta."""
import argparse
import getpass
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from mysql_defaults import defaults_match, default_error


def sql_statements(script):
    """Lê os scripts controlados deste repo, incluindo DELIMITER de rotinas.

    Não é parser SQL genérico. Comentários de linha inteira são ignorados;
    delimitadores aparecem somente no fim das instruções destes arquivos.
    """
    delimiter = ";"
    buffer = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("DELIMITER "):
            if buffer:
                raise ValueError("DELIMITER com instrução incompleta.")
            delimiter = stripped.split()[1]
            continue
        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer).rstrip()[:-len(delimiter)].strip()
            if not re.match(r"^(SET (NAMES|time_zone)|CREATE (TABLE|UNIQUE INDEX|INDEX|FUNCTION|PROCEDURE))\b", statement, re.I):
                raise ValueError("Comando não permitido no inicializador.")
            yield statement
            buffer = []
    if buffer:
        raise ValueError("SQL incompleto no fim do arquivo.")


def prepare_statements():
    from gerar_schema import render_schema
    schema = (ROOT / "backend/database/schema_mysql.sql").read_text(encoding="utf-8")
    if schema != render_schema():
        raise ValueError("Schema divergente dos modelos. Nenhum DDL autorizado.")
    routines = (ROOT / "backend/database/procedures.sql").read_text(encoding="utf-8")
    return list(sql_statements(schema)) + list(sql_statements(routines))


def inventory(cursor, database):
    cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", (database,))
    tables = sorted(row["TABLE_NAME"] for row in cursor.fetchall())
    cursor.execute("SELECT ROUTINE_NAME,ROUTINE_TYPE FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=%s", (database,))
    routines = {row["ROUTINE_NAME"]: row["ROUTINE_TYPE"] for row in cursor.fetchall()}
    return tables, routines


def ensure_empty(cursor, database):
    tables, routines = inventory(cursor, database)
    if tables or routines:
        raise ValueError(f"Banco não vazio. Recusado sem modificar objetos. Tabelas/views: {tables}; rotinas: {sorted(routines)}")


def validate_objects(cursor, database):
    import model_registry
    from database import db
    from sqlalchemy.dialects import mysql
    tables, routines = inventory(cursor, database)
    expected_tables = set(db.metadata.tables)
    if set(tables) != expected_tables:
        raise ValueError(f"Tabelas divergentes: {set(tables) ^ expected_tables}")
    script = (ROOT / "backend/database/procedures.sql").read_text(encoding="utf-8")
    expected_routines = {name: kind.upper() for kind,name in re.findall(r"CREATE (FUNCTION|PROCEDURE) (\w+)", script)}
    if routines != expected_routines:
        raise ValueError("Rotinas ausentes ou inesperadas.")
    cursor.execute("SELECT TABLE_NAME,ENGINE,TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", (database,))
    for row in cursor.fetchall():
        if row["ENGINE"] != "InnoDB" or row["TABLE_COLLATION"] != "utf8mb4_0900_as_ci":
            raise ValueError(f"Engine/collation divergente: {row['TABLE_NAME']}")
    for table in db.metadata.tables.values():
        cursor.execute("SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA,CHARACTER_SET_NAME,COLLATION_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (database,table.name))
        columns = {row["COLUMN_NAME"]: row for row in cursor.fetchall()}
        if set(columns) != set(table.columns.keys()):
            raise ValueError(f"Colunas divergentes: {table.name}")
        for col in table.columns:
            actual = columns[col.name]
            expected_type = str(col.type.compile(dialect=mysql.dialect())).lower().replace("boolean", "tinyint(1)").replace("numeric", "decimal").replace("bool", "tinyint(1)").replace("integer", "int").replace(" ", "")
            actual_type = actual["COLUMN_TYPE"].lower()
            if actual["CHARACTER_SET_NAME"] is not None and (actual["CHARACTER_SET_NAME"] != "utf8mb4" or actual["COLLATION_NAME"] != "utf8mb4_0900_as_ci"):
                raise ValueError(f"Charset/collation divergente: {table.name}.{col.name}")
            if not defaults_match(col, actual["COLUMN_DEFAULT"]):
                raise ValueError(default_error(col, actual["COLUMN_DEFAULT"]))
            if col.primary_key and col.type.python_type is int and "auto_increment" not in actual["EXTRA"]:
                raise ValueError(f"AUTO_INCREMENT ausente: {table.name}.{col.name}")
            if actual_type != expected_type or (actual["IS_NULLABLE"] == "YES") != col.nullable:
                raise ValueError(f"Tipo/nullability divergente: {table.name}.{col.name}: {actual_type} / {expected_type}")
        cursor.execute("""SELECT k.COLUMN_NAME,k.REFERENCED_TABLE_NAME,k.REFERENCED_COLUMN_NAME,r.DELETE_RULE
            FROM information_schema.KEY_COLUMN_USAGE k
            JOIN information_schema.REFERENTIAL_CONSTRAINTS r ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME AND r.TABLE_NAME=k.TABLE_NAME
            WHERE k.TABLE_SCHEMA=%s AND k.TABLE_NAME=%s AND k.REFERENCED_TABLE_NAME IS NOT NULL""", (database,table.name))
        actual_fks = {(r["COLUMN_NAME"],r["REFERENCED_TABLE_NAME"],r["REFERENCED_COLUMN_NAME"],r["DELETE_RULE"]) for r in cursor.fetchall()}
        expected_fks = {(fk.parent.name,fk.column.table.name,fk.column.name,fk.ondelete or "RESTRICT") for fk in table.foreign_keys}
        if actual_fks != expected_fks:
            raise ValueError(f"FKs divergentes: {table.name}")
        cursor.execute("SELECT INDEX_NAME,NON_UNIQUE,COLUMN_NAME,SEQ_IN_INDEX FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY INDEX_NAME,SEQ_IN_INDEX", (database,table.name))
        indexes = {}
        unique = set()
        for row in cursor.fetchall():
            indexes.setdefault(row["INDEX_NAME"], []).append(row["COLUMN_NAME"])
            if row["NON_UNIQUE"] == 0:
                unique.add(row["INDEX_NAME"])
        if indexes.get("PRIMARY") != [c.name for c in table.primary_key.columns]:
            raise ValueError(f"Chave primária divergente: {table.name}")
        actual_unique = {tuple(indexes[name]) for name in unique}
        expected_unique = {tuple(c.name for c in table.primary_key.columns)}
        for constraint in table.constraints:
            if constraint.__class__.__name__ == "UniqueConstraint":
                expected_unique.add(tuple(c.name for c in constraint.columns))
        expected_unique.update(tuple(c.name for c in index.columns) for index in table.indexes if index.unique)
        if actual_unique != expected_unique:
            raise ValueError(f"Unicidades divergentes: {table.name}")
        for index in table.indexes:
            if indexes.get(index.name) != [c.name for c in index.columns]:
                raise ValueError(f"Índice ausente: {index.name}")
    return tables, routines


def initialize(connection, database, confirm=input):
    if database not in {"ifix", "ifix_test"}:
        raise ValueError("Somente ifix ou ifix_test são permitidos.")
    statements = prepare_statements()  # Validar arquivos antes de qualquer DDL.
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE() banco,VERSION() versao")
        info = cursor.fetchone()
        if info["banco"] != database or not info["versao"].startswith("8.4."):
            raise ValueError("Banco selecionado ou versão MySQL diverge do esperado (8.4).")
        cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
        if not cursor.fetchone()["Value"]:
            raise ValueError("Conexão sem TLS recusada.")
        ensure_empty(cursor, database)
        print(f"Destino confirmado: {database}; MySQL {info['versao']}. Sem tabelas/rotinas.")
        if confirm(f"Digite INICIALIZAR {database} para criar a estrutura: ") != f"INICIALIZAR {database}":
            print("Cancelado sem DDL.")
            return False
        ensure_empty(cursor, database)
        created = []
        creation_finished = False
        current_object = "validação"
        try:
            for statement in statements:
                current_object = statement.splitlines()[0].split("(")[0]
                cursor.execute(statement)
                if statement.startswith("CREATE"):
                    created.append(current_object)
                while cursor.nextset():
                    pass
            creation_finished = True
            tables,routines = validate_objects(cursor,database)
        except Exception:
            # DDL MySQL pode fazer commit implícito: nunca prometer rollback.
            print(f"Comandos CREATE concluídos nesta execução: {created}")
            try:
                tables,routines = inventory(cursor,database)
            except Exception:
                tables,routines = ["inventário indisponível: conexão perdida"], {}
            print(f"Última instrução/objeto: {current_object}")
            stage = "CRIAÇÃO CONCLUÍDA; VALIDAÇÃO REPROVADA" if creation_finished else "FALHA PARCIAL"
            print(f"{stage}. Tabelas/views presentes: {tables}; rotinas presentes: {sorted(routines)}")
            print("Interrompido. Nada foi apagado. Não reexecute o inicializador em banco com objetos; use validar_mysql.py.")
            raise
        print(f"VALIDADO: {len(tables)} tabelas, FKs, tipos, nullability, UNIQUEs, índices; {len(routines)} rotinas.")
        print("Tabelas: " + ", ".join(tables))
        print("Rotinas: " + ", ".join(sorted(routines)))
        print("Nenhum registro inicial foi inserido.")
        return True


def prompt_connection(database="ifix"):
    import pymysql
    from mysql_tls import tls_context
    host = input("Host Aiven (DNS do certificado): ").strip()
    port = int(input("Porta: ").strip())
    user = input("Usuário: ").strip()
    selected = input(f"Banco [{database}]: ").strip() or database
    if selected != database:
        raise ValueError(f"Banco deve ser {database}.")
    password = getpass.getpass("Senha (oculta): ")
    ca = input("Caminho do certificado CA: ").strip().strip('"')
    return pymysql.connect(host=host,port=port,user=user,password=password,database=selected,
        charset="utf8mb4",ssl=tls_context(ca_path=ca,ca_pem=None),cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,read_timeout=20,write_timeout=20,autocommit=True,
        init_command="SET time_zone = '+00:00'")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco-teste",action="store_true",help="Inicializar exclusivamente ifix_test, nunca ifix")
    args=parser.parse_args()
    database="ifix_test" if args.banco_teste else "ifix"
    try:
        with prompt_connection(database) as connection:
            initialize(connection,database)
    except (Exception,KeyboardInterrupt) as error:
        # Não exibir connection string ou parâmetros de autenticação.
        print(f"Inicialização interrompida ({type(error).__name__}).")
        if isinstance(error,ValueError):
            print(str(error))
        else:
            code = error.args[0] if error.args and isinstance(error.args[0],int) else "n/a"
            print(f"Código: {code}. Verifique CA, DNS, porta, privilégios e relatório de objetos acima.")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
