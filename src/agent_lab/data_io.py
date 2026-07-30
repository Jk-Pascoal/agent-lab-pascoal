"""Leitura dos dados sintéticos sem dependências externas."""

import csv
from dataclasses import dataclass
from pathlib import Path

from .domain import MaterialRecord


@dataclass(frozen=True, slots=True)
class LabeledMaterial:
    """Material acompanhado do rótulo usado somente na avaliação."""

    record: MaterialRecord
    expected_issue: str


def load_labeled_materials(path: str | Path) -> list[LabeledMaterial]:
    """Carrega o CSV e separa dados de entrada do rótulo de avaliação."""

    materials: list[LabeledMaterial] = []
    with Path(path).open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            record = MaterialRecord(
                material_id=row.get("material_id", "").strip(),
                description_short=row.get("description_short", "").strip(),
                long_description=row.get("long_description", "").strip(),
                unit=row.get("unit", "").strip(),
                manufacturer=row.get("manufacturer", "").strip(),
                manufacturer_part_number=row.get(
                    "manufacturer_part_number", ""
                ).strip(),
                material_group=row.get("material_group", "").strip(),
                status=row.get("status", "").strip(),
            )
            materials.append(
                LabeledMaterial(
                    record=record,
                    expected_issue=row.get("expected_issue", "").strip(),
                )
            )
    return materials

