from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import agent_lab.consistency as consistency
from agent_lab.audit import record_human_review
from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import HumanDecision, VerifiedSpecialistIdentity
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class DualWriteConsistencyIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lifecycle_path = (
            Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        )
        self.audit_path = Path(self.temp_dir.name) / "audit_events.jsonl"

        self.opened_at = datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)
        self.verified_at = datetime(2026, 8, 22, 11, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)

        evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=evidence,
            rationale="Recomendação REVIEW para MAT-001",
            requires_human_decision=True,
        )
        self.opened_event = WorkflowOpened(
            event_id="wf-evt-open-001",
            workflow_id="wf-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )

        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist1@corp.com",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )
        review_result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )
        self.review = review_result.review
        self.audit_event = review_result.audit_event
        self.concluded_event = WorkflowConcluded(
            event_id="wf-evt-conc-001",
            workflow_id="wf-001",
            review=self.review,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ca14_lifecycle_concluded_persisted_without_audit_detected_after_restart(
        self,
    ) -> None:
        # 1. Primeira instância dos repositórios: persiste opened e concluded no lifecycle, mas falha antes do audit
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        audit_repo_1 = JsonlAuditRepository(self.audit_path)

        lifecycle_repo_1.append_opened(self.opened_event)
        lifecycle_repo_1.append_concluded(self.concluded_event)
        # intencionalmente não gravamos no audit_repo_1

        # 2. Simulação de restart de processo com NOVAS instâncias sobre os mesmos arquivos
        lifecycle_repo_2 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        audit_repo_2 = JsonlAuditRepository(self.audit_path)

        # 3. Comprovar que os eventos foram de fato lidos do disco após restart
        persisted_lifecycle_events = lifecycle_repo_2.list_all_events()
        persisted_audit_events = audit_repo_2.list_all()

        self.assertEqual(len(persisted_lifecycle_events), 2)
        self.assertEqual(len(persisted_audit_events), 0)

        # 4. Executar verificação via adapter de repositórios
        report = consistency.verify_repositories_consistency(
            lifecycle_repo_2,
            audit_repo_2,
        )

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 0)
        self.assertEqual(report.matched_pairs_count, 0)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            consistency.ConsistencyIssueType.MISSING_AUDIT_EVENT,
        )
        self.assertEqual(issue.review_id, self.review.review_id)
        self.assertEqual(issue.workflow_id, self.concluded_event.workflow_id)

    def test_ca14_audit_persisted_without_lifecycle_concluded_detected_after_restart(
        self,
    ) -> None:
        # 1. Primeira instância dos repositórios: persiste opened no lifecycle e audit no audit repo, mas não conclui no lifecycle
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        audit_repo_1 = JsonlAuditRepository(self.audit_path)

        lifecycle_repo_1.append_opened(self.opened_event)
        audit_repo_1.append(self.audit_event)
        # intencionalmente não gravamos concluded no lifecycle_repo_1

        # 2. Simulação de restart de processo com NOVAS instâncias sobre os mesmos arquivos
        lifecycle_repo_2 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        audit_repo_2 = JsonlAuditRepository(self.audit_path)

        # 3. Comprovar que os eventos foram de fato lidos do disco após restart
        persisted_lifecycle_events = lifecycle_repo_2.list_all_events()
        persisted_audit_events = audit_repo_2.list_all()

        self.assertEqual(len(persisted_lifecycle_events), 1)
        self.assertEqual(len(persisted_audit_events), 1)

        # 4. Executar verificação via adapter de repositórios
        report = consistency.verify_repositories_consistency(
            lifecycle_repo_2,
            audit_repo_2,
        )

        self.assertEqual(report.total_concluded_events, 0)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 0)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            consistency.ConsistencyIssueType.MISSING_WORKFLOW_CONCLUDED,
        )
        self.assertEqual(issue.review_id, self.review.review_id)
        self.assertEqual(issue.audit_event_id, self.audit_event.event_id)


if __name__ == "__main__":
    unittest.main()
