"""Comparação conservadora de pares dimensionais explícitos.

Somente evidência lexical: não altera o scorer nem decide duplicidade.
"""

from enum import Enum
from fractions import Fraction

from agent_lab.normalization import ordered_dimension_pair


class DimensionPairRelation(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


def compare_ordered_dimensions(first_description: str, second_description: str) -> DimensionPairRelation:
    """Compara somente pares explícitos com unidade em ambas as descrições.

    UNKNOWN cobre falta de unidade, ambiguidade e dimensões não reconhecidas.
    Um mismatch lexical é uma pista para revisão, não rejeição automática.
    """
    first = ordered_dimension_pair(first_description)
    second = ordered_dimension_pair(second_description)
    if first is None or second is None or not first[2] or not second[2]:
        return DimensionPairRelation.UNKNOWN
    # A different unit requires an explicitly governed conversion policy.
    # Without that policy even apparently different numbers are not comparable.
    if first[2] != second[2]:
        return DimensionPairRelation.UNKNOWN
    # Equivalent rational spellings (1/2 and 0.5) must not be called conflicts.
    # Bound numeric lengths before parsing untrusted catalog text.
    values = (*first[:2], *second[:2])
    if any(len(v) > 80 for v in values):
        return DimensionPairRelation.UNKNOWN
    try:
        left = tuple(Fraction(v) for v in first[:2])
        right = tuple(Fraction(v) for v in second[:2])
    except (ValueError, ZeroDivisionError, OverflowError):
        return DimensionPairRelation.UNKNOWN
    return DimensionPairRelation.MATCH if left == right else DimensionPairRelation.MISMATCH
