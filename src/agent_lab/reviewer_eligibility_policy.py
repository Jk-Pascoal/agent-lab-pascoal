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
    if not isinstance(claim_state, HumanReviewClaimState):
        raise TypeError(
            "claim_state must be a HumanReviewClaimState instance"
        )

    if not isinstance(
        reviewer_identity,
        VerifiedSpecialistIdentity,
    ):
        raise TypeError(
            "reviewer_identity must be a VerifiedSpecialistIdentity instance"
        )

    if claim_state.state is HumanReviewClaimFactState.NO_CLAIM:
        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.CLAIM_REQUIRED
        )

    if claim_state.state is HumanReviewClaimFactState.SINGLE_CLAIM:
        sole_claim = claim_state.sole_claim
        if sole_claim is None:
            raise AssertionError(
                "single-claim state must expose a sole claim"
            )

        claimant = sole_claim.specialist

        same_stable_principal = (
            claimant.specialist_id == reviewer_identity.specialist_id
            and claimant.identity_provider
            == reviewer_identity.identity_provider
            and claimant.identity_subject
            == reviewer_identity.identity_subject
        )

        if same_stable_principal:
            return ReviewerEligibilityDecision(
                status=ReviewerEligibilityStatus.ELIGIBLE
            )

        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.CLAIMANT_MISMATCH
        )

    if claim_state.state is HumanReviewClaimFactState.MULTIPLE_CLAIMS:
        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT
        )

    raise AssertionError("unsupported human review claim fact state")
