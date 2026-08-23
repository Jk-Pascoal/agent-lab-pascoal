from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from agent_lab.decision import DecisionRecommendation
from agent_lab.human_review import HumanDecision, HumanReview


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
    predecessor_workflow_id: str | None = None
    triggering_review_id: str | None = None

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

        if self.predecessor_workflow_id is not None:
            sanitized_predecessor_workflow_id = _require_non_blank(
                self.predecessor_workflow_id,
                "predecessor_workflow_id",
            )
            object.__setattr__(
                self,
                "predecessor_workflow_id",
                sanitized_predecessor_workflow_id,
            )

        if self.triggering_review_id is not None:
            sanitized_triggering_review_id = _require_non_blank(
                self.triggering_review_id,
                "triggering_review_id",
            )
            object.__setattr__(
                self,
                "triggering_review_id",
                sanitized_triggering_review_id,
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
        predecessor_workflow_id=workflow.predecessor_workflow_id,
        triggering_review_id=workflow.triggering_review_id,
    )


def open_correction_follow_up(
    predecessor: GovernanceWorkflow,
    *,
    workflow_id: str,
    recommendation: DecisionRecommendation,
    opened_at: datetime,
) -> GovernanceWorkflow:
    """Open a new governance workflow cycle linked to a prior correction review."""
    if not isinstance(predecessor, GovernanceWorkflow):
        raise TypeError("predecessor must be a GovernanceWorkflow")
    if not isinstance(recommendation, DecisionRecommendation):
        raise ValueError("recommendation must be a DecisionRecommendation")
    if predecessor.review is None:
        raise ValueError(
            "predecessor must be reviewed before opening a correction follow-up"
        )
    if (
        predecessor.review.human_decision
        is not HumanDecision.REQUEST_CORRECTION
    ):
        raise ValueError(
            "correction follow-up requires REQUEST_CORRECTION decision"
        )
    sanitized_workflow_id = _require_non_blank(
        workflow_id,
        "workflow_id",
    )
    if sanitized_workflow_id == predecessor.workflow_id:
        raise ValueError(
            "correction follow-up workflow_id must differ from predecessor workflow_id"
        )
    if recommendation.material_id != predecessor.material_id:
        raise ValueError(
            "correction follow-up material_id must match predecessor material_id"
        )
    validated_opened_at = _require_aware_datetime(
        opened_at,
        "opened_at",
    )
    if (
        predecessor.closed_at is not None
        and validated_opened_at < predecessor.closed_at
    ):
        raise ValueError(
            "correction follow-up opened_at cannot be before predecessor closed_at"
        )

    return GovernanceWorkflow(
        workflow_id=sanitized_workflow_id,
        recommendation=recommendation,
        opened_at=validated_opened_at,
        review=None,
        predecessor_workflow_id=predecessor.workflow_id,
        triggering_review_id=predecessor.review.review_id,
    )
