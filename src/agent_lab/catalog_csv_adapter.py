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
        reader = csv.DictReader(
            file,
            restval="",
            strict=True,
        )

        header = reader.fieldnames
        if header is None or not header or not any(header):
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

        records: list[MaterialRecord] = []
        for row in reader:
            if None in row:
                raise ValueError("CSV row contains more fields than header")

            record = MaterialRecord(
                material_id=row["material_id"],
                description_short=row.get("description_short", ""),
                long_description=row.get("long_description", ""),
                unit=row.get("unit", ""),
                manufacturer=row.get("manufacturer", ""),
                manufacturer_part_number=row.get("manufacturer_part_number", ""),
                material_group=row.get("material_group", ""),
                status=row.get("status", ""),
            )
            records.append(record)

        return tuple(records)
