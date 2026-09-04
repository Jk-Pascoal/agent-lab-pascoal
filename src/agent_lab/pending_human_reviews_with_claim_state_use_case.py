from __future__ import annotations

from dataclasses import dataclass

from agent_lab.human_review_claim_projection import HumanReviewClaimState
from agent_lab.workflow import GovernanceWorkflow


@dataclass(frozen=True, slots=True)
class PendingHumanReviewWithClaimStateItem:
    """Immutable composite read-model pairing a pending workflow with its factual claim state."""

    workflow: GovernanceWorkflow
    claim_state: HumanReviewClaimState

    def __post_init__(self) -> None:
        if not isinstance(self.workflow, GovernanceWorkflow) or isinstance(self.workflow, bool):
            raise TypeError("workflow must be a GovernanceWorkflow instance")

        if not isinstance(self.claim_state, HumanReviewClaimState) or isinstance(self.claim_state, bool):
            raise TypeError("claim_state must be a HumanReviewClaimState instance")

        if self.workflow.workflow_id != self.claim_state.workflow_id:
            raise ValueError(
                f"workflow_id mismatch: workflow has {self.workflow.workflow_id!r}, "
                f"claim_state has {self.claim_state.workflow_id!r}"
            )
