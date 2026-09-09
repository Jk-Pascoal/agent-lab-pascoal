from __future__ import annotations

from datetime import datetime

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    release_human_review_claim,
)
from agent_lab.human_review_claim_release_repository import (
    HumanReviewClaimReleaseRepository,
)
from agent_lab.workflow import GovernanceWorkflow


class ReleaseHumanReviewClaimUseCase:
    """Application use case to coordinate releasing a human review claim."""

    def __init__(
        self,
        *,
        claim_release_repository: HumanReviewClaimReleaseRepository,
    ) -> None:
        self._claim_release_repository = claim_release_repository

    def execute(
        self,
        workflow: GovernanceWorkflow,
        claim: HumanReviewClaim,
        *,
        release_id: str,
        releasing_specialist: VerifiedSpecialistIdentity,
        released_at: datetime,
    ) -> HumanReviewClaimRelease:
        release = release_human_review_claim(
            workflow,
            claim,
            release_id=release_id,
            releasing_specialist=releasing_specialist,
            released_at=released_at,
        )

        self._claim_release_repository.append(release)

        return release
