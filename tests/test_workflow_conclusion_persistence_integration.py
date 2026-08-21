from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_projection import rehydrate_workflow
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class WorkflowConclusionPersistenceIntegrationTests(unittest.TestCase):
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
        self.verified_at = datetime(
            2026,
            8,
            19,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            19,
            9,
            30,
            0,
            tzinfo=timezone.utc,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workflow_conclusion_survives_two_restarts_and_rehydrates_reviewed_state(
        self,
    ) -> None:
        evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=evidence,
            rationale="Recomendação REVIEW para MAT-001",
            requires_human_decision=True,
        )
        opened = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=recommendation,
            opened_at=self.opened_at,
        )

        repository_1 = JsonlWorkflowLifecycleRepository(self.file_path)
        repository_1.append_opened(opened)

        # RESTART 1: Nova instância do repositório em processo/sessão posterior
        repository_2 = JsonlWorkflowLifecycleRepository(self.file_path)
        events_after_open = repository_2.get_events_by_workflow_id(
            opened.workflow_id
        )
        pending = rehydrate_workflow(events_after_open)

        self.assertEqual(pending.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(pending.review)
        self.assertIsNone(pending.closed_at)
        self.assertIsNone(pending.review_lead_time)

        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@company.com",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )
        review = HumanReview(
            review_id="rev-wf-mat-001-01",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=self.reviewed_at,
            justification="Aprovado sem ressalvas na auditoria técnica.",
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id=opened.workflow_id,
            review=review,
        )

        # Persistência da conclusão pela instância pós-restart
        repository_2.append_concluded(concluded)

        # RESTART 2: Nova instância do repositório simulando novo reinício
        repository_3 = JsonlWorkflowLifecycleRepository(self.file_path)
        events_after_conclusion = repository_3.get_events_by_workflow_id(
            opened.workflow_id
        )

        self.assertEqual(events_after_conclusion, (opened, concluded))

        reviewed = rehydrate_workflow(events_after_conclusion)

        self.assertEqual(reviewed.status, WorkflowStatus.REVIEWED)
        self.assertEqual(reviewed.review, review)
        self.assertEqual(reviewed.closed_at, review.reviewed_at)
        self.assertEqual(
            reviewed.review_lead_time,
            review.reviewed_at - opened.opened_at,
        )
        self.assertEqual(reviewed.workflow_id, opened.workflow_id)
        self.assertEqual(reviewed.material_id, opened.recommendation.material_id)
        self.assertEqual(reviewed.recommendation, opened.recommendation)


if __name__ == "__main__":
    unittest.main()
