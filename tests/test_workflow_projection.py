from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_projection import rehydrate_pending_workflow


class WorkflowProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.evidence = (
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
            evidence=self.evidence,
            rationale="Recomendação REVIEW: 1 evidência(s) requer(em) análise humana.",
            requires_human_decision=True,
        )
        self.event = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )

    def test_rehydrates_valid_workflow_opened_to_governance_workflow(self) -> None:
        workflow = rehydrate_pending_workflow(self.event)

        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, self.event.workflow_id)
        self.assertEqual(workflow.workflow_id, "wf-mat-001-01")
        self.assertIs(workflow.recommendation, self.event.recommendation)
        self.assertEqual(workflow.opened_at, self.event.opened_at)
        self.assertIsNone(workflow.review)

    def test_rehydrated_workflow_derived_properties(self) -> None:
        workflow = rehydrate_pending_workflow(self.event)

        self.assertEqual(workflow.material_id, "MAT-001")
        self.assertEqual(
            workflow.material_id,
            self.event.recommendation.material_id,
        )
        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rejects_non_workflow_opened_instance_with_type_error(self) -> None:
        with self.assertRaises(TypeError):
            rehydrate_pending_workflow("not-a-workflow-opened")  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            rehydrate_pending_workflow(None)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            rehydrate_pending_workflow(
                {
                    "event_id": "evt-001",
                    "workflow_id": "wf-001",
                    "recommendation": self.recommendation,
                    "opened_at": self.opened_at,
                }
            )  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
