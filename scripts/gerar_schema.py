"""Gera DDL offline dos modelos reais. --check compara; --write grava."""
import argparse
import sys
from pathlib import Path
from sqlalchemy import MetaData, DefaultClause, text
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable, CreateIndex

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

def render_schema():
    import model_registry
    from database import db
    metadata = MetaData()
    for original in db.metadata.sorted_tables:
        table = original.to_metadata(metadata)
        table.dialect_options["mysql"]["engine"] = "InnoDB"
        table.dialect_options["mysql"]["charset"] = "utf8mb4"
        # Case-insensitive e accent-sensitive: mais próximo de ILIKE.
        table.dialect_options["mysql"]["collate"] = "utf8mb4_0900_as_ci"
        for column in table.columns:
            default = column.default
            if default is None:
                continue
            if default.is_scalar:
                arg = default.arg
                literal = str(int(arg)) if isinstance(arg, bool) else str(arg)
                if isinstance(arg, str):
                    literal = "'" + arg.replace("'", "''") + "'"
                column.server_default = DefaultClause(text(literal))
            elif default.is_callable and column.type.python_type.__name__ == "datetime":
                column.server_default = DefaultClause(text("CURRENT_TIMESTAMP(6)"))
    chunks = ["-- Gerado dos 14 modelos por scripts/gerar_schema.py. Sem dados, DROP ou IF NOT EXISTS.",
              "-- Execute somente no schema vazio explicitamente selecionado pelo inicializador.",
              "SET NAMES utf8mb4 COLLATE utf8mb4_0900_as_ci;", "SET time_zone = '+00:00';"]
    dialect = mysql.dialect()
    for table in metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip().splitlines()
        definitions = [line.strip().rstrip(",") for line in ddl[1:-1]]
        constraints = sorted(line for line in definitions if line.startswith(("PRIMARY KEY", "UNIQUE", "CONSTRAINT", "FOREIGN KEY")))
        columns = [line for line in definitions if line not in constraints]
        chunks.append(ddl[0] + "\n\t" + ",\n\t".join(columns + constraints) + "\n" + ddl[-1] + ";")
        for index in sorted(table.indexes, key=lambda item: item.name):
            chunks.append(str(CreateIndex(index).compile(dialect=dialect)) + ";")
    return "\n\n".join(chunks) + "\n"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args()
    path = ROOT / "backend/database/schema_mysql.sql"
    rendered = render_schema()
    if args.check:
        if path.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Schema divergente dos modelos. Revise antes de regenerar.")
        print("Schema corresponde aos 14 modelos.")
    else:
        path.write_text(rendered, encoding="utf-8")

if __name__ == "__main__":
    main()
