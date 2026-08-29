from __future__ import annotations

from typing import Sequence

from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
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
        predecessor_workflow_id=event.predecessor_workflow_id,
        triggering_review_id=event.triggering_review_id,
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
        predecessor_workflow_id=opened.predecessor_workflow_id,
        triggering_review_id=opened.triggering_review_id,
    )


def project_pending_human_review_queue(
    events: Sequence[WorkflowLifecycleEvent],
) -> tuple[GovernanceWorkflow, ...]:
    """Project an ordered queue of workflows currently in PENDING_HUMAN_REVIEW state."""
    if not isinstance(events, Sequence):
        raise TypeError(
            f"events must be a Sequence, got {type(events).__name__}"
        )

    for index, event in enumerate(events):
        if not isinstance(event, (WorkflowOpened, WorkflowConcluded)):
            raise ValueError(
                f"Unsupported lifecycle event type at index {index}: {type(event).__name__}"
            )

    grouped_events: dict[str, list[WorkflowLifecycleEvent]] = {}
    for event in events:
        grouped_events.setdefault(event.workflow_id, []).append(event)

    pending_workflows: list[GovernanceWorkflow] = []
    for workflow_history in grouped_events.values():
        workflow = rehydrate_workflow(workflow_history)
        if workflow.status == WorkflowStatus.PENDING_HUMAN_REVIEW:
            pending_workflows.append(workflow)

    pending_workflows.sort(key=lambda wf: (wf.opened_at, wf.workflow_id))

    return tuple(pending_workflows)
