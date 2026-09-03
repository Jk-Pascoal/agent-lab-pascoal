from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from agent_lab.human_review_claim import HumanReviewClaim


class HumanReviewClaimFactState(str, Enum):
    NO_CLAIM = "NO_CLAIM"
    SINGLE_CLAIM = "SINGLE_CLAIM"
    MULTIPLE_CLAIMS = "MULTIPLE_CLAIMS"


@dataclass(frozen=True, slots=True)
class HumanReviewClaimState:
    workflow_id: str
    claims: tuple[HumanReviewClaim, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or isinstance(self.workflow_id, bool):
            raise TypeError("workflow_id must be a string")
        sanitized_wf = self.workflow_id.strip()
        if not sanitized_wf:
            raise ValueError("workflow_id must not be empty or whitespace")
        if self.workflow_id != sanitized_wf:
            object.__setattr__(self, "workflow_id", sanitized_wf)

        if not isinstance(self.claims, tuple):
            raise TypeError("claims must be a tuple")

        for idx, claim in enumerate(self.claims):
            if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
                raise TypeError(
                    f"claim at index {idx} must be a HumanReviewClaim instance"
                )
            if claim.workflow_id != sanitized_wf:
                raise ValueError(
                    f"claim at index {idx} has workflow_id {claim.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

    @property
    def claim_count(self) -> int:
        return len(self.claims)

    @property
    def state(self) -> HumanReviewClaimFactState:
        if self.claim_count == 0:
            return HumanReviewClaimFactState.NO_CLAIM
        if self.claim_count == 1:
            return HumanReviewClaimFactState.SINGLE_CLAIM
        return HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def is_unclaimed(self) -> bool:
        return self.state is HumanReviewClaimFactState.NO_CLAIM

    @property
    def has_claims(self) -> bool:
        return self.claim_count > 0

    @property
    def has_multiple_claims(self) -> bool:
        return self.state is HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def sole_claim(self) -> HumanReviewClaim | None:
        if self.state is HumanReviewClaimFactState.SINGLE_CLAIM:
            return self.claims[0]
        return None


def project_human_review_claim_state(
    workflow_id: str,
    claims: Sequence[HumanReviewClaim],
) -> HumanReviewClaimState:
    if not isinstance(workflow_id, str) or isinstance(workflow_id, bool):
        raise TypeError("workflow_id must be a string")
    sanitized_wf = workflow_id.strip()
    if not sanitized_wf:
        raise ValueError("workflow_id must not be empty or whitespace")

    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes, bytearray)):
        raise TypeError("claims must be a Sequence of HumanReviewClaim")

    for idx, claim in enumerate(claims):
        if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
            raise TypeError(
                f"claim at index {idx} must be a HumanReviewClaim instance, "
                f"got {type(claim).__name__}"
            )

    filtered = [c for c in claims if c.workflow_id == sanitized_wf]
    sorted_claims = sorted(
        filtered,
        key=lambda claim: (claim.claimed_at, claim.claim_id),
    )
    return HumanReviewClaimState(workflow_id=sanitized_wf, claims=tuple(sorted_claims))
