from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision

SCHEMA_VERSION_V1 = 1


def material_revision_to_record(
    revision: MaterialRevision,
) -> dict[str, object]:
    record_dict: dict[str, object] = {
        "material_id": revision.record.material_id,
        "description_short": revision.record.description_short,
        "long_description": revision.record.long_description,
        "unit": revision.record.unit,
        "manufacturer": revision.record.manufacturer,
        "manufacturer_part_number": revision.record.manufacturer_part_number,
        "material_group": revision.record.material_group,
        "status": revision.record.status,
    }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "revision_id": revision.revision_id,
        "record": record_dict,
        "revised_at": revision.revised_at.isoformat(),
        "predecessor_revision_id": revision.predecessor_revision_id,
        "source_review_id": revision.source_review_id,
    }


def material_revision_from_record(
    record: Mapping[str, Any],
) -> MaterialRevision:
    raw_record = record["record"]
    material_record = MaterialRecord(
        material_id=raw_record["material_id"],
        description_short=raw_record["description_short"],
        long_description=raw_record["long_description"],
        unit=raw_record["unit"],
        manufacturer=raw_record["manufacturer"],
        manufacturer_part_number=raw_record["manufacturer_part_number"],
        material_group=raw_record["material_group"],
        status=raw_record["status"],
    )

    return MaterialRevision(
        revision_id=record["revision_id"],
        record=material_record,
        revised_at=datetime.fromisoformat(record["revised_at"]),
        predecessor_revision_id=record["predecessor_revision_id"],
        source_review_id=record["source_review_id"],
    )
