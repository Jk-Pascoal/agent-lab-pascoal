from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision

SCHEMA_VERSION_V1 = 1

_MATERIAL_RECORD_FIELDS = (
    "material_id",
    "description_short",
    "long_description",
    "unit",
    "manufacturer",
    "manufacturer_part_number",
    "material_group",
    "status",
)


def _validate_material_record_string_fields(record_data: Mapping[str, Any]) -> None:
    for field_name in _MATERIAL_RECORD_FIELDS:
        if field_name not in record_data:
            raise ValueError(f"Missing required field in record: {field_name}")
        val = record_data[field_name]
        if not isinstance(val, str):
            raise ValueError(f"{field_name} must be a string, got {type(val).__name__}")


def _parse_revised_at(raw_revised_at: Any) -> datetime:
    if not isinstance(raw_revised_at, str):
        raise ValueError(
            f"revised_at must be a string, got {type(raw_revised_at).__name__}"
        )
    try:
        dt = datetime.fromisoformat(raw_revised_at)
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 timestamp: {raw_revised_at!r}") from e

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(
            f"revised_at must be timezone-aware, got naive timestamp: {raw_revised_at!r}"
        )
    return dt


def material_revision_to_record(
    revision: MaterialRevision,
) -> dict[str, object]:
    if revision.revised_at.tzinfo is None or revision.revised_at.utcoffset() is None:
        raise ValueError("revised_at must be timezone-aware")

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
    _validate_material_record_string_fields(record_dict)

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
    if not isinstance(record, Mapping):
        raise ValueError("Record must be a Mapping")

    if "schema_version" not in record:
        raise ValueError("schema_version is required")

    schema_version = record["schema_version"]
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    if "revision_id" not in record:
        raise ValueError("revision_id is required")

    if "record" not in record:
        raise ValueError("record is required")

    if "revised_at" not in record:
        raise ValueError("revised_at is required")

    if "predecessor_revision_id" not in record:
        raise ValueError("predecessor_revision_id is required")

    if "source_review_id" not in record:
        raise ValueError("source_review_id is required")

    raw_record = record["record"]
    if not isinstance(raw_record, Mapping):
        raise ValueError("record must be a Mapping")

    _validate_material_record_string_fields(raw_record)
    revised_at = _parse_revised_at(record["revised_at"])

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
        revised_at=revised_at,
        predecessor_revision_id=record["predecessor_revision_id"],
        source_review_id=record["source_review_id"],
    )
