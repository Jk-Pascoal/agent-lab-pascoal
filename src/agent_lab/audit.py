from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any

from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)


class AuditEventType(str, Enum):
    """Types of immutable facts recorded by the audit domain."""

    HUMAN_REVIEW_RECORDED = "HUMAN_REVIEW_RECORDED"


def _require_non_blank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value.strip()


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _freeze(value: Any) -> Any:
    """Create an immutable defensive copy of supported metadata values."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class AuditEvent:
    """Immutable fact that can be appended to an audit history."""

    event_id: str
    event_type: AuditEventType
    material_id: str
    actor_id: str
    occurred_at: datetime
    review_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_non_blank(self.event_id, "event_id"),
        )
        object.__setattr__(
            self,
            "material_id",
            _require_non_blank(self.material_id, "material_id"),
        )
        object.__setattr__(
            self,
            "actor_id",
            _require_non_blank(self.actor_id, "actor_id"),
        )
        object.__setattr__(
            self,
            "review_id",
            _require_non_blank(self.review_id, "review_id"),
        )
        _require_aware_datetime(self.occurred_at, "occurred_at")

        if not isinstance(self.event_type, AuditEventType):
            raise ValueError("event_type must be an AuditEventType")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")

        object.__setattr__(self, "metadata", _freeze(self.metadata))


@dataclass(frozen=True)
class HumanReviewResult:
    """Atomic in-memory result of recording a human review."""

    review: HumanReview
    audit_event: AuditEvent

    def __post_init__(self) -> None:
        if not isinstance(self.review, HumanReview):
            raise ValueError("review must be a HumanReview")
        if not isinstance(self.audit_event, AuditEvent):
            raise ValueError("audit_event must be an AuditEvent")
        if self.audit_event.review_id != self.review.review_id:
            raise ValueError("audit event must reference the same review")
        if self.audit_event.material_id != self.review.material_id:
            raise ValueError("audit event must reference the same material")
        if (
            self.audit_event.actor_id
            != self.review.reviewer_identity.specialist_id
        ):
            raise ValueError("audit event must reference the same reviewer")
        if self.audit_event.occurred_at != self.review.reviewed_at:
            raise ValueError("audit event must use the review timestamp")


def record_human_review(
    *,
    event_id: str,
    review_id: str,
    material_id: str,
    system_recommendation: GovernanceDecision,
    human_decision: HumanDecision,
    reviewer_identity: VerifiedSpecialistIdentity,
    reviewed_at: datetime,
    justification: str | None = None,
    corrections: Iterable[CorrectionRequest] = (),
) -> HumanReviewResult:
    """Build a validated human review and its correlated audit event.

    The function has no persistence or external side effects. If review
    validation fails, no result or audit event is returned.
    """

    review = HumanReview(
        review_id=review_id,
        material_id=material_id,
        system_recommendation=system_recommendation,
        human_decision=human_decision,
        reviewer_identity=reviewer_identity,
        reviewed_at=reviewed_at,
        justification=justification,
        corrections=tuple(corrections),
    )

    audit_event = AuditEvent(
        event_id=event_id,
        event_type=AuditEventType.HUMAN_REVIEW_RECORDED,
        material_id=review.material_id,
        actor_id=review.reviewer_identity.specialist_id,
        occurred_at=review.reviewed_at,
        review_id=review.review_id,
        metadata={
            "system_recommendation": (
                review.system_recommendation.value
            ),
            "human_decision": review.human_decision.value,
            "agrees_with_system": review.agrees_with_system,
            "correction_count": len(review.corrections),
            "identity_provider": (
                review.reviewer_identity.identity_provider
            ),
            "identity_subject": review.reviewer_identity.identity_subject,
            "identity_verification_id": (
                review.reviewer_identity.verification_id
            ),
            "identity_verified_at": (
                review.reviewer_identity.verified_at.isoformat()
            ),
        },
    )

    return HumanReviewResult(
        review=review,
        audit_event=audit_event,
    )

