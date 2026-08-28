from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from agent_lab.audit import AuditEvent, record_human_review
from agent_lab.audit_repository import AuditRepository
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import GovernanceWorkflow, conclude_governance_workflow
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

    def execute(
        self,
        workflow: GovernanceWorkflow,
        *,
        review_id: str,
        audit_event_id: str,
        lifecycle_event_id: str,
        human_decision: HumanDecision,
        reviewer_identity: VerifiedSpecialistIdentity,
        reviewed_at: datetime,
        justification: str | None = None,
        corrections: Iterable[CorrectionRequest] = (),
    ) -> RecordHumanDecisionResult:
        if not isinstance(workflow, GovernanceWorkflow):
            raise TypeError("workflow must be a GovernanceWorkflow")

        # Fase 1 — Domínio / Zero I/O: construção e validação determinística de todos os artefatos
        human_review_result = record_human_review(
            event_id=audit_event_id,
            review_id=review_id,
            material_id=workflow.material_id,
            system_recommendation=workflow.recommendation.decision,
            human_decision=human_decision,
            reviewer_identity=reviewer_identity,
            reviewed_at=reviewed_at,
            justification=justification,
            corrections=corrections,
        )

        concluded_workflow = conclude_governance_workflow(
            workflow, human_review_result.review
        )

        lifecycle_event = WorkflowConcluded(
            event_id=lifecycle_event_id,
            workflow_id=workflow.workflow_id,
            review=human_review_result.review,
        )

        # Fase 2 — Persistência coordenada em ordem estrita
        self._audit_repository.append(human_review_result.audit_event)
        self._workflow_lifecycle_repository.append_concluded(lifecycle_event)

        # Fase 3 — Retorno dos artefatos consolidados
        return RecordHumanDecisionResult(
            workflow=concluded_workflow,
            review=human_review_result.review,
            audit_event=human_review_result.audit_event,
            lifecycle_event=lifecycle_event,
        )
