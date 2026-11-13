"""Comparação conservadora de pares dimensionais explícitos.

Somente evidência lexical: não altera o scorer nem decide duplicidade.
"""

from enum import Enum

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
    if first == second:
        return DimensionPairRelation.MATCH
    return DimensionPairRelation.MISMATCH
