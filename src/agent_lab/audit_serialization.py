from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from agent_lab.audit import AuditEvent, AuditEventType

SCHEMA_VERSION_V1 = 1


def _require_string_field(record: Mapping[str, object], field_name: str) -> str:
    if field_name not in record:
        raise ValueError(f"Missing required field: {field_name}")
    value = record[field_name]
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def audit_event_to_record(event: AuditEvent) -> dict[str, object]:
    """Serialize an immutable AuditEvent into a versioned record dictionary."""

    if not isinstance(event, AuditEvent):
        raise ValueError("event must be an AuditEvent instance")

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "material_id": event.material_id,
        "actor_id": event.actor_id,
        "occurred_at": event.occurred_at.isoformat(),
        "review_id": event.review_id,
        "metadata": dict(event.metadata),
    }


def audit_event_from_record(record: Mapping[str, object]) -> AuditEvent:
    """Deserialize a versioned record mapping into an immutable AuditEvent."""

    if not isinstance(record, Mapping):
        raise ValueError("record must be a Mapping")

    if "schema_version" not in record:
        raise ValueError("schema_version is required")

    schema_version = record["schema_version"]
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    event_id = _require_string_field(record, "event_id")
    material_id = _require_string_field(record, "material_id")
    actor_id = _require_string_field(record, "actor_id")
    review_id = _require_string_field(record, "review_id")

    if "event_type" not in record:
        raise ValueError("Missing required field: event_type")
    raw_event_type = record["event_type"]
    try:
        event_type = AuditEventType(raw_event_type)
    except (ValueError, KeyError) as exc:
        raise ValueError(f"Invalid event_type: {raw_event_type!r}") from exc

    if "occurred_at" not in record:
        raise ValueError("Missing required field: occurred_at")
    raw_occurred_at = record["occurred_at"]
    if isinstance(raw_occurred_at, str):
        try:
            occurred_at = datetime.fromisoformat(raw_occurred_at)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ISO 8601 timestamp: {raw_occurred_at!r}"
            ) from exc
    elif isinstance(raw_occurred_at, datetime):
        occurred_at = raw_occurred_at
    else:
        raise ValueError("occurred_at must be an ISO 8601 string or datetime")

    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("occurred_at must be timezone-aware")

    raw_metadata = record.get("metadata", {})
    if not isinstance(raw_metadata, Mapping):
        raise ValueError("metadata must be a Mapping")

    return AuditEvent(
        event_id=event_id,
        event_type=event_type,
        material_id=material_id,
        actor_id=actor_id,
        occurred_at=occurred_at,
        review_id=review_id,
        metadata=dict(raw_metadata),
    )
