from __future__ import annotations

from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_events import WorkflowOpened


def rehydrate_pending_workflow(event: WorkflowOpened) -> GovernanceWorkflow:
    """Project a WorkflowOpened event into a pending GovernanceWorkflow."""
    if not isinstance(event, WorkflowOpened):
        raise TypeError("event must be a WorkflowOpened instance")

    return GovernanceWorkflow(
        workflow_id=event.workflow_id,
        recommendation=event.recommendation,
        opened_at=event.opened_at,
        review=None,
    )
