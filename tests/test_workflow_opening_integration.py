from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import (
    WorkflowStatus,
    conclude_governance_workflow,
)
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_projection import rehydrate_pending_workflow
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class WorkflowOpeningIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        self.opened_at = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            19,
            9,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            19,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_restart_recovers_pending_workflow_from_persisted_opening(
        self,
    ) -> None:
        evidence = (
            GovernanceEvidence(
                material_id="MAT-0047",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation = DecisionRecommendation(
            material_id="MAT-0047",
            decision=GovernanceDecision.REVIEW,
            evidence=evidence,
            rationale="Snapshot original da recomendação para MAT-0047.",
            requires_human_decision=True,
        )
        event = WorkflowOpened(
            event_id="evt-open-0047",
            workflow_id="wf-0047",
            recommendation=recommendation,
            opened_at=self.opened_at,
        )

        repository_instance_1 = JsonlWorkflowLifecycleRepository(self.file_path)
        repository_instance_1.append_opened(event)

        # SIMULAR RESTART: nova instância em memória apontando para o mesmo arquivo
        repository_instance_2 = JsonlWorkflowLifecycleRepository(self.file_path)
        recovered = repository_instance_2.get_opened_by_workflow_id("wf-0047")

        self.assertIsNotNone(recovered)
        assert recovered is not None  # type narrowing
        self.assertEqual(recovered, event)
        self.assertIsNot(recovered, event)
        self.assertEqual(recovered.recommendation, recommendation)
        self.assertEqual(recovered.recommendation.evidence, evidence)
        self.assertEqual(
            recovered.recommendation.rationale,
            "Snapshot original da recomendação para MAT-0047.",
        )
        self.assertEqual(recovered.opened_at, self.opened_at)

        workflow = rehydrate_pending_workflow(recovered)

        self.assertEqual(workflow.workflow_id, "wf-0047")
        self.assertEqual(workflow.material_id, "MAT-0047")
        self.assertEqual(workflow.recommendation, recommendation)
        self.assertEqual(workflow.opened_at, self.opened_at)
        self.assertIsNone(workflow.review)
        self.assertEqual(workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rehydrated_pending_workflow_can_be_concluded_by_valid_human_review(
        self,
    ) -> None:
        evidence = (
            GovernanceEvidence(
                material_id="MAT-0047",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation = DecisionRecommendation(
            material_id="MAT-0047",
            decision=GovernanceDecision.REVIEW,
            evidence=evidence,
            rationale="Snapshot original da recomendação para MAT-0047.",
            requires_human_decision=True,
        )
        event = WorkflowOpened(
            event_id="evt-open-0047",
            workflow_id="wf-0047",
            recommendation=recommendation,
            opened_at=self.opened_at,
        )

        repository_instance_1 = JsonlWorkflowLifecycleRepository(self.file_path)
        repository_instance_1.append_opened(event)

        # SIMULAR RESTART
        repository_instance_2 = JsonlWorkflowLifecycleRepository(self.file_path)
        recovered = repository_instance_2.get_opened_by_workflow_id("wf-0047")
        self.assertIsNotNone(recovered)
        assert recovered is not None

        rehydrated = rehydrate_pending_workflow(recovered)

        reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-0047",
            identity_provider="corporate-idp",
            identity_subject="specialist-0047@corp.local",
            verification_id="verification-0047",
            verified_at=self.verified_at,
        )

        corrections = (
            CorrectionRequest(
                field_name="description",
                reason="Campo crítico precisa ser corrigido.",
                suggested_value="Descrição técnica revisada.",
            ),
        )

        review = HumanReview(
            review_id="review-0047",
            material_id="MAT-0047",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.REQUEST_CORRECTION,
            reviewer_identity=reviewer_identity,
            reviewed_at=self.reviewed_at,
            justification="Justificativa da revisão com solicitação de correção.",
            corrections=corrections,
        )

        concluded = conclude_governance_workflow(rehydrated, review)

        self.assertIsNot(concluded, rehydrated)
        self.assertEqual(
            rehydrated.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(rehydrated.review)

        self.assertEqual(concluded.workflow_id, rehydrated.workflow_id)
        self.assertEqual(concluded.recommendation, rehydrated.recommendation)
        self.assertEqual(concluded.status, WorkflowStatus.REVIEWED)
        self.assertEqual(concluded.review, review)
        self.assertEqual(concluded.closed_at, self.reviewed_at)
        self.assertEqual(
            concluded.review_lead_time,
            self.reviewed_at - self.opened_at,
        )
        self.assertEqual(
            concluded.review_lead_time,
            timedelta(minutes=45),
        )


if __name__ == "__main__":
    unittest.main()
