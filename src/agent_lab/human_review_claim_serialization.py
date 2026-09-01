from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim

SCHEMA_VERSION_V1 = 1

_ROOT_REQUIRED_FIELDS = frozenset(
    {"schema_version", "claim_id", "workflow_id", "specialist", "claimed_at"}
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


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"Field {field_name!r} must be a string, got {type(value).__name__}"
        )
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"Field {field_name!r} must not be empty or whitespace")
    return trimmed


def _parse_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str):
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
    if not isinstance(data, Mapping):
        raise ValueError(
            f"Field 'specialist' must be a Mapping, got {type(data).__name__}"
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

    specialist_id = _require_non_empty_str(data["specialist_id"], "specialist_id")
    identity_provider = _require_non_empty_str(
        data["identity_provider"], "identity_provider"
    )
    identity_subject = _require_non_empty_str(
        data["identity_subject"], "identity_subject"
    )
    verification_id = _require_non_empty_str(
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


def human_review_claim_to_record(claim: HumanReviewClaim) -> dict[str, object]:
    """Serialize an immutable HumanReviewClaim into a canonical versioned record dictionary."""
    if not isinstance(claim, HumanReviewClaim):
        raise ValueError("claim must be a HumanReviewClaim instance")

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "claim_id": claim.claim_id,
        "workflow_id": claim.workflow_id,
        "specialist": {
            "specialist_id": claim.specialist.specialist_id,
            "identity_provider": claim.specialist.identity_provider,
            "identity_subject": claim.specialist.identity_subject,
            "verification_id": claim.specialist.verification_id,
            "verified_at": claim.specialist.verified_at.isoformat(),
        },
        "claimed_at": claim.claimed_at.isoformat(),
    }


def human_review_claim_from_record(
    record: Mapping[str, object],
) -> HumanReviewClaim:
    """Deserialize a versioned record mapping into an immutable HumanReviewClaim."""
    if not isinstance(record, Mapping):
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
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    claim_id = _require_non_empty_str(record["claim_id"], "claim_id")
    workflow_id = _require_non_empty_str(record["workflow_id"], "workflow_id")
    specialist = _parse_specialist(record["specialist"])
    claimed_at = _parse_iso_datetime(record["claimed_at"], "claimed_at")

    if specialist.verified_at > claimed_at:
        raise ValueError("specialist verification must not be after claimed_at")

    return HumanReviewClaim(
        claim_id=claim_id,
        workflow_id=workflow_id,
        specialist=specialist,
        claimed_at=claimed_at,
    )
