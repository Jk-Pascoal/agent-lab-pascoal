from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
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
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_projection import project_pending_human_review_queue
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class PendingReviewQueueProjectionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"

        self.verified_at = datetime(
            2026,
            8,
            19,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.opened_at_1 = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at_1 = datetime(
            2026,
            8,
            19,
            9,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.opened_at_fup = datetime(
            2026,
            8,
            19,
            9,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.opened_at_later = datetime(
            2026,
            8,
            19,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )

        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@company.com",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )

        self.evidence_1 = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório ausente.",
                severity=IssueSeverity.WARNING,
            ),
        )
        self.recommendation_1 = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence_1,
            rationale="Recomendação REVIEW MAT-001.",
            requires_human_decision=True,
        )

        self.evidence_2 = (
            GovernanceEvidence(
                material_id="MAT-002",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Documentação pendente.",
                severity=IssueSeverity.WARNING,
            ),
        )
        self.recommendation_2 = DecisionRecommendation(
            material_id="MAT-002",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence_2,
            rationale="Recomendação REVIEW MAT-002.",
            requires_human_decision=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_pending_review_queue_projection_post_restart_with_jsonl_repository(
        self,
    ) -> None:
        repository = JsonlWorkflowLifecycleRepository(self.file_path)

        # 1. Workflow 1: Aberto e Concluído com REQUEST_CORRECTION
        opened_1 = WorkflowOpened(
            event_id="evt-open-01",
            workflow_id="wf-root-01",
            recommendation=self.recommendation_1,
            opened_at=self.opened_at_1,
        )
        correction_1 = CorrectionRequest(
            field_name="description",
            reason="Necessário ajuste cadastral.",
        )
        review_1 = HumanReview(
            review_id="rev-01",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.REQUEST_CORRECTION,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at_1,
            justification="Solicitada correção de dados.",
            corrections=(correction_1,),
        )
        concluded_1 = WorkflowConcluded(
            event_id="evt-conc-01",
            workflow_id="wf-root-01",
            review=review_1,
        )
        repository.append_opened(opened_1)
        repository.append_concluded(concluded_1)

        # 2. Workflow 2: Correction Follow-up (Pendente)
        opened_2 = WorkflowOpened(
            event_id="evt-open-02",
            workflow_id="wf-root-01-fup",
            recommendation=self.recommendation_1,
            opened_at=self.opened_at_fup,
            predecessor_workflow_id="wf-root-01",
            triggering_review_id="rev-01",
        )
        repository.append_opened(opened_2)

        # 3. Workflow 3: Raiz Pendente
        opened_3 = WorkflowOpened(
            event_id="evt-open-03",
            workflow_id="wf-root-03",
            recommendation=self.recommendation_2,
            opened_at=self.opened_at_later,
        )
        repository.append_opened(opened_3)

        # 4. Workflow 4: Raiz Pendente com mesmo opened_at de Workflow 3 (para tie-break)
        opened_4 = WorkflowOpened(
            event_id="evt-open-04",
            workflow_id="wf-root-02",
            recommendation=self.recommendation_2,
            opened_at=self.opened_at_later,
        )
        repository.append_opened(opened_4)

        # 5. Simulação de Restart de Processo
        del repository
        restarted_repository = JsonlWorkflowLifecycleRepository(self.file_path)

        # 6. Recuperação e Projeção
        events = restarted_repository.list_all_events()
        queue = project_pending_human_review_queue(events)

        # 7. Asserções de Contrato Pós-Restart
        self.assertIsInstance(queue, tuple)
        self.assertEqual(len(queue), 3)

        # Exclusão do concluído e ordem canônica (opened_at ASC, workflow_id ASC)
        workflow_ids = [wf.workflow_id for wf in queue]
        self.assertNotIn("wf-root-01", workflow_ids)
        self.assertEqual(
            workflow_ids,
            ["wf-root-01-fup", "wf-root-02", "wf-root-03"],
        )

        # Estados de pendência e ausência de review
        for wf in queue:
            self.assertIsInstance(wf, GovernanceWorkflow)
            self.assertEqual(wf.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
            self.assertIsNone(wf.review)

        # Preservação de linhagem pós-serialização/reload
        fup_workflow = queue[0]
        self.assertEqual(fup_workflow.workflow_id, "wf-root-01-fup")
        self.assertEqual(fup_workflow.predecessor_workflow_id, "wf-root-01")
        self.assertEqual(fup_workflow.triggering_review_id, "rev-01")
        self.assertEqual(fup_workflow.material_id, "MAT-001")


if __name__ == "__main__":
    unittest.main()
