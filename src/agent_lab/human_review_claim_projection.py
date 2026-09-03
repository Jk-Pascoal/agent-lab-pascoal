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
        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty or whitespace")

        if not isinstance(self.claims, tuple):
            raise TypeError("claims must be a tuple")

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
    filtered = tuple(c for c in claims if c.workflow_id == workflow_id)
    return HumanReviewClaimState(workflow_id=workflow_id, claims=filtered)
