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
