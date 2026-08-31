from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.workflow import GovernanceWorkflow


@dataclass(frozen=True, slots=True)
class HumanReviewClaim:
    claim_id: str
    workflow_id: str
    specialist: VerifiedSpecialistIdentity
    claimed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, str):
            raise TypeError("claim_id must be a string")

        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")

        if not isinstance(self.workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")

        if not isinstance(self.specialist, VerifiedSpecialistIdentity):
            raise TypeError("specialist must be a VerifiedSpecialistIdentity")

        if not isinstance(self.claimed_at, datetime):
            raise TypeError("claimed_at must be a datetime")

        if self.claimed_at.tzinfo is None or self.claimed_at.utcoffset() is None:
            raise ValueError("claimed_at must be timezone-aware")

        if self.specialist.verified_at > self.claimed_at:
            raise ValueError(
                "specialist verification must not be after claimed_at"
            )


def claim_pending_human_review(
    workflow: GovernanceWorkflow,
    *,
    claim_id: str,
    specialist: VerifiedSpecialistIdentity,
    claimed_at: datetime,
) -> HumanReviewClaim:
    return HumanReviewClaim(
        claim_id=claim_id,
        workflow_id=workflow.workflow_id,
        specialist=specialist,
        claimed_at=claimed_at,
    )
