from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_lab.audit import (
    AuditEventType,
    HumanReviewResult,
    record_human_review,
)
from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import (
    GovernanceWorkflow,
    WorkflowStatus,
    conclude_governance_workflow,
)


class WorkflowIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "audit_history.jsonl"
        self.repository = JsonlAuditRepository(self.file_path)

        self.verified_at = datetime(
            2026,
            8,
            18,
            9,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            45,
            0,
            tzinfo=timezone.utc,
        )

        self.material_id = "MAT-PASCOAL-0044"
        self.workflow_id = "wf-20260818-001"
        self.review_id = "rev-20260818-001"
        self.event_id = "audit-event-20260818-001"

        self.reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-98765",
            verified_at=self.verified_at,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_end_to_end_workflow_conclusion_and_audit_persistence(
        self,
    ) -> None:
        recommendation = DecisionRecommendation(
            material_id=self.material_id,
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação APPROVE para teste de integração.",
            requires_human_decision=True,
        )

        workflow = GovernanceWorkflow(
            workflow_id=self.workflow_id,
            recommendation=recommendation,
            opened_at=self.opened_at,
            review=None,
        )

        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertEqual(workflow.material_id, self.material_id)
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

        result: HumanReviewResult = record_human_review(
            event_id=self.event_id,
            review_id=self.review_id,
            material_id=self.material_id,
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.reviewer_identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        concluded_workflow = conclude_governance_workflow(
            workflow,
            result.review,
        )

        self.assertIsNot(concluded_workflow, workflow)
        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow.review)

        self.assertEqual(
            concluded_workflow.status,
            WorkflowStatus.REVIEWED,
        )
        self.assertEqual(
            concluded_workflow.workflow_id,
            self.workflow_id,
        )
        self.assertEqual(
            concluded_workflow.material_id,
            self.material_id,
        )
        self.assertEqual(
            concluded_workflow.recommendation,
            recommendation,
        )
        self.assertEqual(
            concluded_workflow.opened_at,
            self.opened_at,
        )
        self.assertEqual(
            concluded_workflow.review,
            result.review,
        )
        self.assertEqual(
            concluded_workflow.closed_at,
            self.reviewed_at,
        )
        self.assertEqual(
            concluded_workflow.review_lead_time,
            timedelta(minutes=45),
        )
        self.assertEqual(
            concluded_workflow.review_lead_time,
            self.reviewed_at - self.opened_at,
        )

        self.repository.append(result.audit_event)

        with self.file_path.open("r", encoding="utf-8") as file:
            raw_lines = [line.strip() for line in file if line.strip()]
        self.assertEqual(len(raw_lines), 1)
        raw_record = json.loads(raw_lines[0])

        self.assertNotIn("workflow_id", raw_record)
        self.assertNotIn("opened_at", raw_record)
        self.assertNotIn("review_lead_time", raw_record)

        reopened_repo = JsonlAuditRepository(self.file_path)
        retrieved_event = reopened_repo.get_by_id(self.event_id)

        self.assertIsNotNone(retrieved_event)
        self.assertEqual(retrieved_event, result.audit_event)
        self.assertEqual(retrieved_event.event_id, self.event_id)
        self.assertEqual(
            retrieved_event.event_type,
            AuditEventType.HUMAN_REVIEW_RECORDED,
        )
        self.assertEqual(retrieved_event.material_id, self.material_id)
        self.assertEqual(retrieved_event.review_id, self.review_id)
        self.assertEqual(
            retrieved_event.actor_id,
            self.reviewer_identity.specialist_id,
        )
        self.assertEqual(retrieved_event.occurred_at, self.reviewed_at)

        self.assertNotIn("workflow_id", retrieved_event.metadata)
        self.assertNotIn("opened_at", retrieved_event.metadata)
        self.assertNotIn("review_lead_time", retrieved_event.metadata)


if __name__ == "__main__":
    unittest.main()
