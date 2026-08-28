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
from agent_lab.workflow import GovernanceWorkflow, conclude_governance_workflow
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

    def test_execute_approves_pending_workflow_and_persists_both_repositories(
        self,
    ) -> None:
        audit_repo = Mock()
        lifecycle_repo = Mock()

        call_order: list[str] = []
        audit_repo.append.side_effect = lambda event: call_order.append("audit")
        lifecycle_repo.append_concluded.side_effect = (
            lambda event: call_order.append("lifecycle")
        )

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
        )

        result = use_case.execute(
            self.workflow,
            review_id="rev-001",
            audit_event_id="evt-aud-001",
            lifecycle_event_id="evt-life-001",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        # 1. Validação do workflow concluído
        self.assertEqual(result.workflow.status.value, "REVIEWED")
        self.assertEqual(result.workflow.workflow_id, self.workflow.workflow_id)
        self.assertEqual(result.workflow.material_id, self.workflow.material_id)
        self.assertEqual(result.workflow.closed_at, self.reviewed_at)

        # 2. Validação da revisão humana
        self.assertEqual(result.review.review_id, "rev-001")
        self.assertEqual(result.review.material_id, "MAT-001")
        self.assertEqual(result.review.human_decision, HumanDecision.APPROVE)
        self.assertEqual(
            result.review.system_recommendation, GovernanceDecision.APPROVE
        )
        self.assertEqual(result.review.reviewer_identity, self.identity)
        self.assertEqual(result.review.reviewed_at, self.reviewed_at)
        self.assertIs(result.workflow.review, result.review)

        # 3. Validação do evento de auditoria
        self.assertEqual(result.audit_event.event_id, "evt-aud-001")
        self.assertEqual(
            result.audit_event.event_type,
            AuditEventType.HUMAN_REVIEW_RECORDED,
        )
        self.assertEqual(result.audit_event.material_id, "MAT-001")
        self.assertEqual(
            result.audit_event.actor_id, self.identity.specialist_id
        )
        self.assertEqual(result.audit_event.review_id, "rev-001")
        self.assertEqual(result.audit_event.occurred_at, self.reviewed_at)

        # 4. Validação do evento de ciclo de vida
        self.assertEqual(result.lifecycle_event.event_id, "evt-life-001")
        self.assertEqual(
            result.lifecycle_event.workflow_id, self.workflow.workflow_id
        )
        self.assertIs(result.lifecycle_event.review, result.review)

        # 5. Validação da persistência sequencial (ordem e argumentos)
        self.assertEqual(call_order, ["audit", "lifecycle"])
        audit_repo.append.assert_called_once_with(result.audit_event)
        lifecycle_repo.append_concluded.assert_called_once_with(
            result.lifecycle_event
        )

    def test_execute_rejects_already_concluded_workflow_via_domain_rule_before_io(
        self,
    ) -> None:
        audit_repo = Mock()
        lifecycle_repo = Mock()

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
        )

        reviewed_workflow = conclude_governance_workflow(
            self.workflow, self.review
        )

        with self.assertRaises(ValueError):
            use_case.execute(
                reviewed_workflow,
                review_id="rev-002",
                audit_event_id="evt-aud-002",
                lifecycle_event_id="evt-life-002",
                human_decision=HumanDecision.APPROVE,
                reviewer_identity=self.identity,
                reviewed_at=self.reviewed_at,
                justification=None,
                corrections=(),
            )

        audit_repo.append.assert_not_called()
        lifecycle_repo.append_concluded.assert_not_called()

    def test_execute_propagates_human_review_domain_violations_before_io(
        self,
    ) -> None:
        audit_repo = Mock()
        lifecycle_repo = Mock()

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
        )

        with self.assertRaises(ValueError):
            use_case.execute(
                self.workflow,
                review_id="rev-003",
                audit_event_id="evt-aud-003",
                lifecycle_event_id="evt-life-003",
                human_decision=HumanDecision.REJECT,
                reviewer_identity=self.identity,
                reviewed_at=self.reviewed_at,
                justification=None,
                corrections=(),
            )

        audit_repo.append.assert_not_called()
        lifecycle_repo.append_concluded.assert_not_called()

    def test_execute_rejects_non_governance_workflow_argument_with_type_error(
        self,
    ) -> None:
        audit_repo = Mock()
        lifecycle_repo = Mock()

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
        )

        with self.assertRaises(TypeError):
            use_case.execute(
                "not-a-workflow",  # type: ignore[arg-type]
                review_id="rev-004",
                audit_event_id="evt-aud-004",
                lifecycle_event_id="evt-life-004",
                human_decision=HumanDecision.APPROVE,
                reviewer_identity=self.identity,
                reviewed_at=self.reviewed_at,
                justification=None,
                corrections=(),
            )

        audit_repo.append.assert_not_called()
        lifecycle_repo.append_concluded.assert_not_called()


if __name__ == "__main__":
    unittest.main()
