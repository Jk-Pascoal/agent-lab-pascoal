"""Métricas simples que formarão o baseline do projeto."""

from collections.abc import Iterable

from .domain import MaterialRecord


DEFAULT_REQUIRED_FIELDS = (
    "material_id",
    "description_short",
    "unit",
    "status",
)


def completeness_score(
    record: MaterialRecord,
    required_fields: Iterable[str] = DEFAULT_REQUIRED_FIELDS,
) -> float:
    """Calcula a proporção de campos obrigatórios preenchidos."""

    fields = tuple(required_fields)
    if not fields:
        raise ValueError("required_fields não pode ser vazio")

    filled = sum(bool(str(getattr(record, name, "")).strip()) for name in fields)
    return filled / len(fields)

