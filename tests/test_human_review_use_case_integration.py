from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.consistency import verify_repositories_consistency
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    HumanDecision,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_use_case import RecordHumanDecisionUseCase
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_projection import rehydrate_workflow
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class HumanReviewUseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audit_path = Path(self.temp_dir.name) / "audit.jsonl"
        self.lifecycle_path = (
            Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        )

        self.verified_at = datetime(2026, 8, 28, 8, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 8, 28, 8, 30, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(2026, 8, 28, 9, 30, 0, tzinfo=timezone.utc)

        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )

        self.evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório pendente de validação.",
                severity=IssueSeverity.WARNING,
            ),
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence,
            rationale="Recomendação REVIEW para MAT-001",
            requires_human_decision=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_use_case_integration_with_real_jsonl_repositories_survives_restart_and_rehydrates_reviewed_state(
        self,
    ) -> None:
        # 1. Setup inicial de repositórios e abertura do workflow no lifecycle
        audit_repo_1 = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        opened = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo_1.append_opened(opened)

        # 2. Obtenção do workflow pendente via projeção
        events_opened = lifecycle_repo_1.get_events_by_workflow_id(
            "wf-mat-001-01"
        )
        pending_workflow = rehydrate_workflow(events_opened)
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        # 3. Execução do caso de uso de aplicação com repositórios reais
        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo_1,
            workflow_lifecycle_repository=lifecycle_repo_1,
        )

        result = use_case.execute(
            pending_workflow,
            review_id="rev-001",
            audit_event_id="evt-aud-001",
            lifecycle_event_id="evt-conc-001",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        self.assertEqual(result.workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(result.review.human_decision, HumanDecision.APPROVE)

        # 4. Simulação de restart: descarte das instâncias e nova instanciação sobre os mesmos arquivos
        del audit_repo_1
        del lifecycle_repo_1
        del use_case

        audit_repo_2 = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_2 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        # 5. Comprovação da persistência física de auditoria após restart
        persisted_audit = audit_repo_2.get_by_id("evt-aud-001")
        self.assertIsNotNone(persisted_audit)
        self.assertEqual(persisted_audit, result.audit_event)

        # 6. Comprovação da persistência física e reidratação do ciclo de vida após restart
        events_after_restart = lifecycle_repo_2.get_events_by_workflow_id(
            "wf-mat-001-01"
        )
        self.assertEqual(len(events_after_restart), 2)
        self.assertEqual(events_after_restart[0], opened)
        self.assertEqual(events_after_restart[1], result.lifecycle_event)

        rehydrated_workflow = rehydrate_workflow(events_after_restart)
        self.assertEqual(rehydrated_workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(rehydrated_workflow.review, result.review)
        self.assertEqual(rehydrated_workflow.closed_at, self.reviewed_at)
        self.assertEqual(rehydrated_workflow.workflow_id, "wf-mat-001-01")
        self.assertEqual(rehydrated_workflow.material_id, "MAT-001")
        self.assertEqual(
            rehydrated_workflow.review_lead_time,
            self.reviewed_at - self.opened_at,
        )

    def test_use_case_integration_maintains_dual_write_consistency_report_clean(
        self,
    ) -> None:
        # 1. Setup de repositórios reais
        audit_repo = JsonlAuditRepository(self.audit_path)
        lifecycle_repo = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        opened = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-mat-001-02",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo.append_opened(opened)

        pending_workflow = rehydrate_workflow(
            lifecycle_repo.get_events_by_workflow_id("wf-mat-001-02")
        )

        # 2. Execução do caso de uso
        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
        )

        use_case.execute(
            pending_workflow,
            review_id="rev-002",
            audit_event_id="evt-aud-002",
            lifecycle_event_id="evt-conc-002",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        # 3. Verificação de consistência cruzada dual-write pós-execução
        report = verify_repositories_consistency(
            lifecycle_repo=lifecycle_repo,
            audit_repo=audit_repo,
        )

        self.assertTrue(report.is_consistent)
        self.assertEqual(report.issue_count, 0)
        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())


if __name__ == "__main__":
    unittest.main()
