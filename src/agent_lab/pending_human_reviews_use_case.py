from __future__ import annotations

from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_projection import project_pending_human_review_queue
from agent_lab.workflow_repository import WorkflowLifecycleRepository


class ListPendingHumanReviewsUseCase:
    """Application use case to list workflows currently pending human review."""

    def __init__(
        self,
        *,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
    ) -> None:
        self._workflow_lifecycle_repository = workflow_lifecycle_repository

    def execute(self) -> tuple[GovernanceWorkflow, ...]:
        events = self._workflow_lifecycle_repository.list_all_events()
        return project_pending_human_review_queue(events)
