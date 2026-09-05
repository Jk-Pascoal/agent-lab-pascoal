from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
)


class ReviewerEligibilityStatus(str, Enum):
    """Canonical status of a reviewer eligibility evaluation against claim state."""

    ELIGIBLE = "ELIGIBLE"
    CLAIM_REQUIRED = "CLAIM_REQUIRED"
    CLAIMANT_MISMATCH = "CLAIMANT_MISMATCH"
    MULTIPLE_CLAIMS_CONFLICT = "MULTIPLE_CLAIMS_CONFLICT"


@dataclass(frozen=True, slots=True)
class ReviewerEligibilityDecision:
    """Immutable decision reflecting normative reviewer eligibility."""

    status: ReviewerEligibilityStatus

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReviewerEligibilityStatus):
            raise TypeError(
                "status must be a ReviewerEligibilityStatus instance"
            )

    @property
    def is_eligible(self) -> bool:
        return self.status is ReviewerEligibilityStatus.ELIGIBLE

    @property
    def reason(self) -> str:
        if self.status is ReviewerEligibilityStatus.ELIGIBLE:
            return "Reviewer matches claimant stable principal on single claim."
        if self.status is ReviewerEligibilityStatus.CLAIM_REQUIRED:
            return "Workflow has no claim recorded; claim is required prior to review."
        if self.status is ReviewerEligibilityStatus.CLAIMANT_MISMATCH:
            return "Reviewer stable principal does not match sole claimant."
        if self.status is ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT:
            return (
                "Workflow has multiple claims; operational conflict "
                "must be resolved externally."
            )
        raise AssertionError("unsupported reviewer eligibility status")


def evaluate_reviewer_claim_eligibility(
    claim_state: HumanReviewClaimState,
    reviewer_identity: VerifiedSpecialistIdentity,
) -> ReviewerEligibilityDecision:
    if claim_state.state is HumanReviewClaimFactState.NO_CLAIM:
        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.CLAIM_REQUIRED
        )

    raise NotImplementedError(
        "reviewer eligibility for claimed workflows is not implemented yet"
    )
