from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaimRelease

SCHEMA_VERSION_V1 = 1

_ROOT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "release_id",
        "claim_id",
        "workflow_id",
        "released_by",
        "released_at",
    }
)

_SPECIALIST_REQUIRED_FIELDS = frozenset(
    {
        "specialist_id",
        "identity_provider",
        "identity_subject",
        "verification_id",
        "verified_at",
    }
)


def _require_sanitized_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"Field {field_name!r} must be a string, got {type(value).__name__}"
        )
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"Field {field_name!r} must not be empty or whitespace")
    return trimmed


def _require_exact_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"Field {field_name!r} must be a string, got {type(value).__name__}"
        )
    if not value.strip():
        raise ValueError(f"Field {field_name!r} must not be empty or whitespace")
    return value


def _parse_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"Field {field_name!r} must be an ISO 8601 string, got {type(value).__name__}"
        )
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 timestamp for {field_name!r}: {value!r}"
        ) from exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(
            f"Timestamp for {field_name!r} must be timezone-aware: {value!r}"
        )
    return dt


def _parse_specialist(data: Any) -> VerifiedSpecialistIdentity:
    if not isinstance(data, Mapping) or isinstance(data, bool):
        raise ValueError(
            f"Field 'released_by' must be a Mapping, got {type(data).__name__}"
        )

    actual_keys = set(data.keys())
    missing = _SPECIALIST_REQUIRED_FIELDS - actual_keys
    if missing:
        raise ValueError(
            f"Missing required specialist field(s): {sorted(missing)}"
        )

    unknown = actual_keys - _SPECIALIST_REQUIRED_FIELDS
    if unknown:
        raise ValueError(
            f"Unknown specialist field(s) detected: {sorted(unknown)}"
        )

    specialist_id = _require_sanitized_non_empty_str(
        data["specialist_id"], "specialist_id"
    )
    identity_provider = _require_sanitized_non_empty_str(
        data["identity_provider"], "identity_provider"
    )
    identity_subject = _require_sanitized_non_empty_str(
        data["identity_subject"], "identity_subject"
    )
    verification_id = _require_sanitized_non_empty_str(
        data["verification_id"], "verification_id"
    )
    verified_at = _parse_iso_datetime(data["verified_at"], "verified_at")

    return VerifiedSpecialistIdentity(
        specialist_id=specialist_id,
        identity_provider=identity_provider,
        identity_subject=identity_subject,
        verification_id=verification_id,
        verified_at=verified_at,
    )


def human_review_claim_release_to_record(
    release: HumanReviewClaimRelease,
) -> dict[str, object]:
    """Serialize an immutable HumanReviewClaimRelease into a canonical versioned record dictionary."""
    if not isinstance(release, HumanReviewClaimRelease) or isinstance(
        release, bool
    ):
        raise ValueError("release must be a HumanReviewClaimRelease instance")

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "release_id": release.release_id,
        "claim_id": release.claim_id,
        "workflow_id": release.workflow_id,
        "released_by": {
            "specialist_id": release.released_by.specialist_id,
            "identity_provider": release.released_by.identity_provider,
            "identity_subject": release.released_by.identity_subject,
            "verification_id": release.released_by.verification_id,
            "verified_at": release.released_by.verified_at.isoformat(),
        },
        "released_at": release.released_at.isoformat(),
    }


def human_review_claim_release_from_record(
    record: Mapping[str, object],
) -> HumanReviewClaimRelease:
    """Deserialize a versioned record mapping into an immutable HumanReviewClaimRelease."""
    if not isinstance(record, Mapping) or isinstance(record, bool):
        raise ValueError(
            f"Record must be a Mapping, got {type(record).__name__}"
        )

    actual_keys = set(record.keys())
    missing = _ROOT_REQUIRED_FIELDS - actual_keys
    if missing:
        raise ValueError(f"Missing required field(s): {sorted(missing)}")

    unknown = actual_keys - _ROOT_REQUIRED_FIELDS
    if unknown:
        raise ValueError(f"Unknown field(s) detected: {sorted(unknown)}")

    schema_version = record["schema_version"]
    if (
        type(schema_version) is not int
        or isinstance(schema_version, bool)
        or schema_version != SCHEMA_VERSION_V1
    ):
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    release_id = _require_sanitized_non_empty_str(
        record["release_id"], "release_id"
    )
    claim_id = _require_exact_non_empty_str(record["claim_id"], "claim_id")
    workflow_id = _require_exact_non_empty_str(
        record["workflow_id"], "workflow_id"
    )
    released_by = _parse_specialist(record["released_by"])
    released_at = _parse_iso_datetime(record["released_at"], "released_at")

    if released_by.verified_at > released_at:
        raise ValueError(
            "released_by verification must not be after released_at"
        )

    return HumanReviewClaimRelease(
        release_id=release_id,
        claim_id=claim_id,
        workflow_id=workflow_id,
        released_by=released_by,
        released_at=released_at,
    )
