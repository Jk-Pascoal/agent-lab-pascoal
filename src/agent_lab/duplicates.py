"""Detecção lexical de possíveis duplicidades para o baseline."""

from .domain import MaterialRecord
from .normalization import (
    category_token,
    normalize_text,
    numeric_tokens,
    word_tokens,
)


def _full_description(record: MaterialRecord) -> str:
    return f"{record.description_short} {record.long_description}".strip()


def is_possible_duplicate(
    incoming: MaterialRecord,
    existing: MaterialRecord,
) -> bool:
    """Compara um novo material com um registro já existente."""

    if incoming.material_id == existing.material_id:
        return False

    incoming_part = normalize_text(incoming.manufacturer_part_number)
    existing_part = normalize_text(existing.manufacturer_part_number)
    incoming_manufacturer = normalize_text(incoming.manufacturer)
    existing_manufacturer = normalize_text(existing.manufacturer)

    if (
        incoming_part
        and incoming_part == existing_part
        and incoming_manufacturer
        and incoming_manufacturer == existing_manufacturer
    ):
        return True

    if normalize_text(incoming.material_group) != normalize_text(
        existing.material_group
    ):
        return False

    incoming_description = _full_description(incoming)
    existing_description = _full_description(existing)

    if category_token(incoming_description) != category_token(existing_description):
        return False

    shared_numbers = numeric_tokens(incoming_description) & numeric_tokens(
        existing_description
    )
    shared_words = word_tokens(incoming_description) & word_tokens(existing_description)

    return len(shared_numbers) >= 2 and len(shared_words) >= 1


def find_duplicate_candidates(
    incoming: MaterialRecord,
    existing_records: list[MaterialRecord],
) -> tuple[str, ...]:
    """Retorna IDs anteriores que podem representar o mesmo material."""

    return tuple(
        record.material_id
        for record in existing_records
        if is_possible_duplicate(incoming, record)
    )

