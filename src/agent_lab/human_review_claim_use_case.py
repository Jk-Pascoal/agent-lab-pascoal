from __future__ import annotations

from datetime import datetime

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    claim_pending_human_review,
)
from agent_lab.human_review_claim_repository import HumanReviewClaimRepository
from agent_lab.workflow import GovernanceWorkflow


class RecordHumanReviewClaimUseCase:
    """Application use case to coordinate recording a human review claim."""

    def __init__(
        self,
        *,
        claim_repository: HumanReviewClaimRepository,
    ) -> None:
        self._claim_repository = claim_repository

    def execute(
        self,
        workflow: GovernanceWorkflow,
        *,
        claim_id: str,
        specialist: VerifiedSpecialistIdentity,
        claimed_at: datetime,
    ) -> HumanReviewClaim:
        if not isinstance(workflow, GovernanceWorkflow):
            raise TypeError("workflow must be a GovernanceWorkflow")

        claim = claim_pending_human_review(
            workflow,
            claim_id=claim_id,
            specialist=specialist,
            claimed_at=claimed_at,
        )

        self._claim_repository.append(claim)

        return claim
