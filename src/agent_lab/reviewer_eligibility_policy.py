from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
    ReleaseAwareClaimState,
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


def _same_stable_principal(
    left: VerifiedSpecialistIdentity,
    right: VerifiedSpecialistIdentity,
) -> bool:
    return (
        left.specialist_id == right.specialist_id
        and left.identity_provider == right.identity_provider
        and left.identity_subject == right.identity_subject
    )


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

        if _same_stable_principal(claimant, reviewer_identity):
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


def evaluate_release_aware_reviewer_claim_eligibility(
    release_aware_state: ReleaseAwareClaimState,
    reviewer_identity: VerifiedSpecialistIdentity,
) -> ReviewerEligibilityDecision:
    if not isinstance(release_aware_state, ReleaseAwareClaimState):
        raise TypeError(
            "release_aware_state must be a ReleaseAwareClaimState instance"
        )

    if not isinstance(
        reviewer_identity,
        VerifiedSpecialistIdentity,
    ):
        raise TypeError(
            "reviewer_identity must be a VerifiedSpecialistIdentity instance"
        )

    if (
        release_aware_state.unreleased_claim_state
        is HumanReviewClaimFactState.NO_CLAIM
    ):
        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.CLAIM_REQUIRED
        )

    if (
        release_aware_state.unreleased_claim_state
        is HumanReviewClaimFactState.SINGLE_CLAIM
    ):
        sole_unreleased_claim = release_aware_state.sole_unreleased_claim
        if sole_unreleased_claim is None:
            raise AssertionError(
                "single-unreleased-claim state must expose a sole unreleased claim"
            )

        claimant = sole_unreleased_claim.specialist

        if _same_stable_principal(claimant, reviewer_identity):
            return ReviewerEligibilityDecision(
                status=ReviewerEligibilityStatus.ELIGIBLE
            )

        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.CLAIMANT_MISMATCH
        )

    if (
        release_aware_state.unreleased_claim_state
        is HumanReviewClaimFactState.MULTIPLE_CLAIMS
    ):
        return ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT
        )

    raise AssertionError("unsupported human review claim fact state")
