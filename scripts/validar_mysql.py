"""Diagnóstico SOMENTE LEITURA de ifix/ifix_test já inicializado.

Não chama initialize/ensure_empty, não instala rotinas e não executa correções.
"""
import argparse
import re
from inicializar_mysql import prompt_connection, validate_objects
from mysql_defaults import defaults_match, expected_default


class ReadOnlyCursor:
    """Impede que o diagnóstico/shared validator envie DDL, DML ou CALL."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, params=None):
        if not re.match(r"^\s*(SELECT|SHOW)\b", sql, re.I):
            raise ValueError("Diagnóstico recusou comando que não é SELECT/SHOW.")
        return self.cursor.execute(sql, params)

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()


def diagnose(connection, database="ifix", show_correction=False, emit=print):
    if database not in {"ifix", "ifix_test"}:
        raise ValueError("Banco permitido: ifix ou ifix_test.")
    import model_registry
    from database import db
    errors = []
    with connection.cursor() as raw:
        cursor = ReadOnlyCursor(raw)
        cursor.execute("SELECT DATABASE() banco, VERSION() versao")
        info = cursor.fetchone()
        if info["banco"] != database or not info["versao"].startswith("8.4."):
            raise ValueError("Banco selecionado/versão divergente; esperado MySQL 8.4.")
        cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
        if not cursor.fetchone()["Value"]:
            raise ValueError("Conexão sem TLS recusada.")
        emit(f"DIAGNÓSTICO SOMENTE LEITURA: {database}; MySQL {info['versao']}")
        cursor.execute("""SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT
            FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s
            ORDER BY TABLE_NAME,ORDINAL_POSITION""", (database,))
        actual_columns = {(row["TABLE_NAME"],row["COLUMN_NAME"]):row for row in cursor.fetchall()}
        emit("Defaults: esperado (modelo/DDL) | observado (MySQL) | resultado")
        for table in db.metadata.sorted_tables:
            for column in table.columns:
                row = actual_columns.get((table.name,column.name))
                if row is None:
                    errors.append(f"Coluna ausente: {table.name}.{column.name}")
                    continue
                matches = defaults_match(column,row["COLUMN_DEFAULT"])
                if column.default is not None or not matches:
                    emit(f"{table.name}.{column.name}: {expected_default(column)!r} | {row['COLUMN_DEFAULT']!r} | {'OK' if matches else 'DIVERGENTE'}")
                if not matches:
                    errors.append(f"Default divergente: {table.name}.{column.name}")
        # Mantém a validação estrutural completa compartilhada com o inicializador.
        try:
            tables,routines = validate_objects(cursor,database)
            emit(f"Estrutura validada: {len(tables)} tabelas e {len(routines)} rotinas; tipos, defaults, nullability, índices, FKs e collation.")
        except ValueError as error:
            errors.append(str(error))
        if show_correction:
            row = actual_columns.get(("servicos","preco_estimado"))
            column = db.metadata.tables["servicos"].c.preco_estimado
            if row and not defaults_match(column,row["COLUMN_DEFAULT"]):
                correct_type = row["COLUMN_TYPE"].lower().replace(" ", "") == "decimal(10,2)"
                if correct_type and row["IS_NULLABLE"] == "NO":
                    emit("SUGESTÃO APENAS, NÃO EXECUTADA: há default diferente/ausente nessa coluna DECIMAL(10,2) NOT NULL.")
                    emit("Efeito: fixa o default para futuros INSERTs que omitam a coluna; não altera valores existentes, tipo, nullability, FKs ou rotinas. DDL pode obter metadata lock e faz commit implícito.")
                    emit(f"ALTER TABLE `{database}`.`servicos` ALTER COLUMN `preco_estimado` SET DEFAULT 0.00;")
                else:
                    emit("Sem sugestão automática: tipo/nullability também divergem; revisar o diagnóstico antes de preparar SQL.")
            else:
                emit("Nenhuma correção SQL de preco_estimado necessária/sugerida: default equivalente ou coluna ausente (revisar erros).")
        if errors:
            emit("DIVERGÊNCIAS ENCONTRADAS (nenhum objeto alterado):")
            for message in dict.fromkeys(errors):
                emit("- " + message)
            return False
        emit("VALIDAÇÃO APROVADA. Nenhuma alteração executada. Não reexecute o inicializador.")
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco-teste",action="store_true",help="Validar ifix_test em vez de ifix")
    parser.add_argument("--mostrar-sql-correcao",action="store_true",help="Somente imprimir SQL mínimo se o default de preco_estimado realmente divergir")
    args = parser.parse_args()
    database = "ifix_test" if args.banco_teste else "ifix"
    try:
        with prompt_connection(database) as connection:
            approved = diagnose(connection,database,args.mostrar_sql_correcao)
    except (Exception,KeyboardInterrupt) as error:
        print(f"Diagnóstico interrompido ({type(error).__name__}); nenhum DDL/DML foi enviado pelo diagnóstico.")
        if isinstance(error,ValueError):
            print(str(error))
        else:
            code = error.args[0] if error.args and isinstance(error.args[0],int) else "n/a"
            print(f"Código: {code}. Verifique conexão, CA e permissões de leitura de metadados.")
        raise SystemExit(1)
    raise SystemExit(0 if approved else 1)

if __name__ == "__main__":
    main()
