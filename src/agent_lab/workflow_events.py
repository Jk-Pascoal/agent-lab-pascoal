from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias

from agent_lab.decision import DecisionRecommendation
from agent_lab.human_review import HumanReview


def _require_non_blank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value.strip()


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True)
class WorkflowOpened:
    """Immutable domain event representing the opening of a governance workflow."""

    event_id: str
    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    predecessor_workflow_id: str | None = None
    triggering_review_id: str | None = None

    def __post_init__(self) -> None:
        sanitized_event_id = _require_non_blank(self.event_id, "event_id")
        object.__setattr__(self, "event_id", sanitized_event_id)

        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.recommendation, DecisionRecommendation):
            raise ValueError("recommendation must be a DecisionRecommendation")

        _require_aware_datetime(self.opened_at, "opened_at")

        has_pred = self.predecessor_workflow_id is not None
        has_trig = self.triggering_review_id is not None

        if has_pred != has_trig:
            raise ValueError(
                "predecessor_workflow_id and triggering_review_id must both be provided or both be None"
            )

        if has_pred:
            sanitized_pred = _require_non_blank(
                self.predecessor_workflow_id, "predecessor_workflow_id"
            )
            if sanitized_pred == sanitized_workflow_id:
                raise ValueError(
                    "predecessor_workflow_id must differ from workflow_id"
                )
            object.__setattr__(
                self, "predecessor_workflow_id", sanitized_pred
            )

        if has_trig:
            sanitized_trig = _require_non_blank(
                self.triggering_review_id, "triggering_review_id"
            )
            object.__setattr__(
                self, "triggering_review_id", sanitized_trig
            )


@dataclass(frozen=True, slots=True)
class WorkflowConcluded:
    """Immutable domain event representing the conclusion of a governance workflow."""

    event_id: str
    workflow_id: str
    review: HumanReview

    def __post_init__(self) -> None:
        sanitized_event_id = _require_non_blank(self.event_id, "event_id")
        object.__setattr__(self, "event_id", sanitized_event_id)

        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.review, HumanReview):
            raise ValueError("review must be a HumanReview instance")


WorkflowLifecycleEvent: TypeAlias = WorkflowOpened | WorkflowConcluded
