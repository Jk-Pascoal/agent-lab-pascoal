from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable

from agent_lab.domain import GovernanceDecision


class HumanDecision(str, Enum):
    """Final action recorded by the human governance specialist."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"


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


@dataclass(frozen=True)
class CorrectionRequest:
    """Structured correction requested by a human reviewer."""

    field_name: str
    reason: str
    suggested_value: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field_name",
            _require_non_blank(self.field_name, "field_name"),
        )
        object.__setattr__(
            self,
            "reason",
            _require_non_blank(self.reason, "reason"),
        )

        if self.suggested_value is not None:
            if not isinstance(self.suggested_value, str):
                raise ValueError("suggested_value must be a string or None")
            object.__setattr__(
                self,
                "suggested_value",
                self.suggested_value.strip(),
            )


@dataclass(frozen=True)
class VerifiedSpecialistIdentity:
    """Immutable verifiable identity contract for a human specialist."""

    specialist_id: str
    identity_provider: str
    identity_subject: str
    verification_id: str
    verified_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_blank(self.specialist_id, "specialist_id"),
        )
        object.__setattr__(
            self,
            "identity_provider",
            _require_non_blank(self.identity_provider, "identity_provider"),
        )
        object.__setattr__(
            self,
            "identity_subject",
            _require_non_blank(self.identity_subject, "identity_subject"),
        )
        object.__setattr__(
            self,
            "verification_id",
            _require_non_blank(self.verification_id, "verification_id"),
        )
        _require_aware_datetime(self.verified_at, "verified_at")


@dataclass(frozen=True)
class HumanReview:
    """Immutable link between a system recommendation and a human decision."""

    review_id: str
    material_id: str
    system_recommendation: GovernanceDecision
    human_decision: HumanDecision
    reviewer_id: str
    reviewed_at: datetime
    justification: str | None = None
    corrections: tuple[CorrectionRequest, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "review_id",
            _require_non_blank(self.review_id, "review_id"),
        )
        object.__setattr__(
            self,
            "material_id",
            _require_non_blank(self.material_id, "material_id"),
        )
        object.__setattr__(
            self,
            "reviewer_id",
            _require_non_blank(self.reviewer_id, "reviewer_id"),
        )
        _require_aware_datetime(self.reviewed_at, "reviewed_at")

        if not isinstance(self.system_recommendation, GovernanceDecision):
            raise ValueError(
                "system_recommendation must be a GovernanceDecision"
            )
        if not isinstance(self.human_decision, HumanDecision):
            raise ValueError("human_decision must be a HumanDecision")

        normalized_corrections = self._normalize_corrections(self.corrections)
        object.__setattr__(self, "corrections", normalized_corrections)

        normalized_justification = self._normalize_justification(
            self.justification
        )
        object.__setattr__(
            self,
            "justification",
            normalized_justification,
        )

        self._validate_decision_rules()

    @staticmethod
    def _normalize_corrections(
        corrections: Iterable[CorrectionRequest],
    ) -> tuple[CorrectionRequest, ...]:
        if isinstance(corrections, (str, bytes)):
            raise ValueError(
                "corrections must be an iterable of CorrectionRequest"
            )

        try:
            normalized = tuple(corrections)
        except TypeError as exc:
            raise ValueError(
                "corrections must be an iterable of CorrectionRequest"
            ) from exc

        if not all(
            isinstance(correction, CorrectionRequest)
            for correction in normalized
        ):
            raise ValueError(
                "corrections must contain only CorrectionRequest values"
            )

        return normalized

    @staticmethod
    def _normalize_justification(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("justification must be a string or None")
        return value.strip()

    def _validate_decision_rules(self) -> None:
        requires_justification = self.human_decision in {
            HumanDecision.REJECT,
            HumanDecision.REQUEST_CORRECTION,
        }

        if requires_justification and not self.justification:
            raise ValueError(
                f"{self.human_decision.value} requires justification"
            )

        if (
            self.human_decision is HumanDecision.REQUEST_CORRECTION
            and not self.corrections
        ):
            raise ValueError(
                "REQUEST_CORRECTION requires at least one correction"
            )

        if (
            self.human_decision is HumanDecision.APPROVE
            and self.corrections
        ):
            raise ValueError("APPROVE cannot include corrections")

    @property
    def agrees_with_system(self) -> bool:
        agreement_pairs = {
            (
                GovernanceDecision.APPROVE,
                HumanDecision.APPROVE,
            ),
            (
                GovernanceDecision.REJECT,
                HumanDecision.REJECT,
            ),
            (
                GovernanceDecision.REVIEW,
                HumanDecision.REQUEST_CORRECTION,
            ),
        }
        return (
            self.system_recommendation,
            self.human_decision,
        ) in agreement_pairs

