from __future__ import annotations

from typing import Sequence

from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
    WorkflowOpened,
)


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


def rehydrate_workflow(
    events: Sequence[WorkflowLifecycleEvent],
) -> GovernanceWorkflow:
    """Project an ordered sequence of lifecycle events into a GovernanceWorkflow."""
    if not events:
        raise ValueError("events sequence cannot be empty")

    for event in events:
        if not isinstance(event, (WorkflowOpened, WorkflowConcluded)):
            raise ValueError(
                f"Unsupported lifecycle event type: {type(event).__name__}"
            )

    if not isinstance(events[0], WorkflowOpened):
        raise ValueError("First event in workflow history must be WorkflowOpened")

    opened_events = [
        event for event in events if isinstance(event, WorkflowOpened)
    ]
    if len(opened_events) != 1:
        raise ValueError(
            f"Expected exactly one WorkflowOpened event, got {len(opened_events)}"
        )

    concluded_events = [
        event for event in events if isinstance(event, WorkflowConcluded)
    ]
    if len(concluded_events) > 1:
        raise ValueError(
            f"Expected at most one WorkflowConcluded event, got {len(concluded_events)}"
        )

    if len(events) not in (1, 2):
        raise ValueError(
            f"Unexpected number of events for workflow lifecycle: {len(events)}"
        )

    opened = events[0]

    if len(events) == 1:
        return rehydrate_pending_workflow(opened)

    concluded = events[1]
    if not isinstance(concluded, WorkflowConcluded):
        raise ValueError(
            "Second event in reviewed workflow history must be WorkflowConcluded"
        )

    if concluded.workflow_id != opened.workflow_id:
        raise ValueError(
            f"workflow_id mismatch between opened '{opened.workflow_id}' and concluded '{concluded.workflow_id}'"
        )

    return GovernanceWorkflow(
        workflow_id=opened.workflow_id,
        recommendation=opened.recommendation,
        opened_at=opened.opened_at,
        review=concluded.review,
    )
