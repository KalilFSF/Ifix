"""Comparação semântica dos defaults do DDL IFix com information_schema.

Não avalia expressões SQL nem converte valores monetários para float.
"""
import re
from decimal import Decimal, InvalidOperation
from sqlalchemy import Boolean, DateTime, Integer, Numeric, Float
from sqlalchemy.dialects import mysql


def expected_default(column):
    default = column.default
    if default is None:
        return None
    if default.is_scalar:
        return int(default.arg) if isinstance(default.arg, bool) else default.arg
    if default.is_callable and isinstance(column.type, DateTime):
        precision = column.type.dialect_impl(mysql.dialect()).fsp or 0
        return f"CURRENT_TIMESTAMP({precision})"
    raise ValueError(f"Default não suportado na validação: {column.table.name}.{column.name}")


def numeric_literal(value):
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text):
        raise ValueError("Default não é literal numérico.")
    number = Decimal(text)
    if not number.is_finite():
        raise ValueError("Default numérico não finito.")
    return number


def timestamp_precision(value):
    match = re.fullmatch(r"\s*(?:CURRENT_TIMESTAMP|NOW)\s*(?:\(\s*([0-6]?)\s*\))?\s*", str(value), re.I)
    return int(match.group(1) or 0) if match else None


def defaults_match(column, actual):
    expected = expected_default(column)
    if actual is None or expected is None:
        # SQL NULL (ou ausência de DEFAULT) não é zero, texto vazio ou 'NULL'.
        return actual is None and expected is None
    if isinstance(column.type, (Boolean, Integer, Numeric, Float)):
        try:
            return numeric_literal(actual) == numeric_literal(expected)
        except (InvalidOperation, ValueError, UnicodeError):
            return False
    if isinstance(column.type, DateTime) and column.default.is_callable:
        actual_precision = timestamp_precision(actual)
        return actual_precision is not None and actual_precision == timestamp_precision(expected)
    if isinstance(actual, bytes):
        actual = actual.decode("utf-8")
    # Não baixar a caixa nem remover espaços de defaults textuais.
    return str(actual) == str(expected)


def default_error(column, actual):
    return (f"Default divergente: {column.table.name}.{column.name}: "
            f"esperado={expected_default(column)!r}; observado={actual!r}; "
            f"tipo={column.type.compile(dialect=mysql.dialect())}")
