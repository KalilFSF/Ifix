"""Decimal durante validação e cálculo; conversão numérica apenas na saída."""
from decimal import Decimal, InvalidOperation

def decimal_value(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Valor monetário inválido.") from None
    if not result.is_finite():
        raise ValueError("Valor monetário não finito.")
    return result
