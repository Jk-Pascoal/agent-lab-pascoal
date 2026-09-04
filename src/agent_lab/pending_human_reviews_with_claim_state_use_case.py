from __future__ import annotations

from dataclasses import dataclass

from agent_lab.human_review_claim_projection import (
    HumanReviewClaimState,
    project_human_review_claim_state,
)
from agent_lab.human_review_claim_repository import HumanReviewClaimRepository
from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_projection import project_pending_human_review_queue
from agent_lab.workflow_repository import WorkflowLifecycleRepository


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


class ListPendingHumanReviewsWithClaimStateUseCase:
    """Application use case composing the pending workflow queue with factual claim states."""

    def __init__(
        self,
        *,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
        claim_repository: HumanReviewClaimRepository,
    ) -> None:
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
        self._claim_repository = claim_repository

    def execute(self) -> tuple[PendingHumanReviewWithClaimStateItem, ...]:
        events_snapshot = self._workflow_lifecycle_repository.list_all_events()
        pending_workflows = project_pending_human_review_queue(events_snapshot)
        claims_snapshot = self._claim_repository.list_all()

        return tuple(
            PendingHumanReviewWithClaimStateItem(
                workflow=workflow,
                claim_state=project_human_review_claim_state(
                    workflow.workflow_id,
                    claims_snapshot,
                ),
            )
            for workflow in pending_workflows
        )
