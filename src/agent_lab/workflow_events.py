from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.decision import DecisionRecommendation


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
