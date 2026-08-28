from __future__ import annotations

from dataclasses import dataclass

from agent_lab.audit import AuditEvent
from agent_lab.audit_repository import AuditRepository
from agent_lab.human_review import HumanReview
from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_events import WorkflowConcluded
from agent_lab.workflow_repository import WorkflowLifecycleRepository


@dataclass(frozen=True, slots=True)
class RecordHumanDecisionResult:
    """Immutable result structure containing the artifacts of a recorded human decision."""

    workflow: GovernanceWorkflow
    review: HumanReview
    audit_event: AuditEvent
    lifecycle_event: WorkflowConcluded


class RecordHumanDecisionUseCase:
    """Application use case to coordinate recording a human decision on a governance workflow."""

    def __init__(
        self,
        *,
        audit_repository: AuditRepository,
        workflow_lifecycle_repository: WorkflowLifecycleRepository,
    ) -> None:
        self._audit_repository = audit_repository
        self._workflow_lifecycle_repository = workflow_lifecycle_repository
