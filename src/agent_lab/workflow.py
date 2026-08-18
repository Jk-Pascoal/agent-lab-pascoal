from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from agent_lab.decision import DecisionRecommendation
from agent_lab.human_review import HumanReview


class WorkflowStatus(str, Enum):
    """Lifecycle states of a material governance workflow."""

    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    REVIEWED = "REVIEWED"


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
class GovernanceWorkflow:
    """Immutable temporal container for a governance review cycle."""

    workflow_id: str
    recommendation: DecisionRecommendation
    opened_at: datetime
    review: HumanReview | None = None

    def __post_init__(self) -> None:
        sanitized_workflow_id = _require_non_blank(
            self.workflow_id, "workflow_id"
        )
        object.__setattr__(self, "workflow_id", sanitized_workflow_id)

        if not isinstance(self.recommendation, DecisionRecommendation):
            raise ValueError("recommendation must be a DecisionRecommendation")

        _require_aware_datetime(self.opened_at, "opened_at")

        if self.review is not None:
            if not isinstance(self.review, HumanReview):
                raise ValueError("review must be a HumanReview")

            if self.review.material_id != self.recommendation.material_id:
                raise ValueError(
                    "review material_id must match recommendation material_id"
                )

            if (
                self.review.system_recommendation
                != self.recommendation.decision
            ):
                raise ValueError(
                    "review system_recommendation must match recommendation decision"
                )

            if self.review.reviewed_at < self.opened_at:
                raise ValueError(
                    "review reviewed_at cannot be earlier than workflow opened_at"
                )

    @property
    def material_id(self) -> str:
        return self.recommendation.material_id

    @property
    def status(self) -> WorkflowStatus:
        if self.review is None:
            return WorkflowStatus.PENDING_HUMAN_REVIEW
        return WorkflowStatus.REVIEWED

    @property
    def closed_at(self) -> datetime | None:
        if self.review is None:
            return None
        return self.review.reviewed_at

    @property
    def review_lead_time(self) -> timedelta | None:
        if self.review is None:
            return None
        return self.review.reviewed_at - self.opened_at


def conclude_governance_workflow(
    workflow: GovernanceWorkflow,
    review: HumanReview,
) -> GovernanceWorkflow:
    """Produce a new GovernanceWorkflow with the human review applied."""
    if not isinstance(workflow, GovernanceWorkflow):
        raise TypeError("workflow must be a GovernanceWorkflow")

    if workflow.review is not None:
        raise ValueError(
            f"Workflow {workflow.workflow_id} is already reviewed"
        )

    return GovernanceWorkflow(
        workflow_id=workflow.workflow_id,
        recommendation=workflow.recommendation,
        opened_at=workflow.opened_at,
        review=review,
    )
