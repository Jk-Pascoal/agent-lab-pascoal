"""Adaptador de infraestrutura para ingestão de catálogos CSV operacionais."""

import csv
from pathlib import Path

from .domain import MaterialRecord

_CANONICAL_COLUMNS: frozenset[str] = frozenset(
    {
        "material_id",
        "description_short",
        "long_description",
        "unit",
        "manufacturer",
        "manufacturer_part_number",
        "material_group",
        "status",
    }
)


def load_catalog_materials(
    path: str | Path,
) -> tuple[MaterialRecord, ...]:
    """Carrega um arquivo CSV operacional de catálogo e mapeia suas linhas para MaterialRecord."""
    resolved_path = Path(path)
    if resolved_path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {resolved_path}")

    with resolved_path.open(encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty or missing header")

        if not header or not any(header):
            raise ValueError("CSV file is empty or missing header")

        if len(header) != len(set(header)):
            seen: set[str] = set()
            duplicates: list[str] = []
            for col in header:
                if col in seen and col not in duplicates:
                    duplicates.append(col)
                seen.add(col)
            raise ValueError(
                f"CSV header contains duplicate column names: {', '.join(duplicates)}"
            )

        if "material_id" not in header:
            raise ValueError("CSV header missing required column: 'material_id'")

        unrecognized = sorted(set(header) - _CANONICAL_COLUMNS)
        if unrecognized:
            raise ValueError(
                f"CSV header contains unrecognized column(s): {', '.join(unrecognized)}"
            )

        try:
            next(reader)
        except StopIteration:
            return ()

        raise NotImplementedError("CSV record mapping is not implemented in Slice 1")
