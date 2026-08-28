from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest
from unittest.mock import Mock

from agent_lab.audit import AuditEvent, AuditEventType
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_use_case import (
    RecordHumanDecisionResult,
    RecordHumanDecisionUseCase,
)
from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_events import WorkflowConcluded


class HumanReviewUseCasePublicContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_audit_repo = Mock()
        self.dummy_lifecycle_repo = Mock()

        self.verified_at = datetime(2026, 8, 28, 9, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 8, 28, 9, 30, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(2026, 8, 28, 10, 0, 0, tzinfo=timezone.utc)

        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação APPROVE",
            requires_human_decision=True,
        )

        self.workflow = GovernanceWorkflow(
            workflow_id="wf-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            review=None,
        )

        self.review = HumanReview(
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        self.audit_event = AuditEvent(
            event_id="evt-aud-001",
            event_type=AuditEventType.HUMAN_REVIEW_RECORDED,
            material_id="MAT-001",
            actor_id="spec-001",
            occurred_at=self.reviewed_at,
            review_id="rev-001",
            metadata={},
        )

        self.lifecycle_event = WorkflowConcluded(
            event_id="evt-life-001",
            workflow_id="wf-001",
            review=self.review,
        )

    def test_record_human_decision_use_case_initialization(self) -> None:
        use_case = RecordHumanDecisionUseCase(
            audit_repository=self.dummy_audit_repo,
            workflow_lifecycle_repository=self.dummy_lifecycle_repo,
        )
        self.assertIsInstance(use_case, RecordHumanDecisionUseCase)

    def test_record_human_decision_result_structure_and_immutability(self) -> None:
        result = RecordHumanDecisionResult(
            workflow=self.workflow,
            review=self.review,
            audit_event=self.audit_event,
            lifecycle_event=self.lifecycle_event,
        )

        self.assertIs(result.workflow, self.workflow)
        self.assertIs(result.review, self.review)
        self.assertIs(result.audit_event, self.audit_event)
        self.assertIs(result.lifecycle_event, self.lifecycle_event)

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            result.workflow = self.workflow  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
