import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class GovernanceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação APPROVE para teste.",
            requires_human_decision=True,
        )

    def build_workflow(self, **overrides) -> GovernanceWorkflow:
        values = {
            "workflow_id": "wf-001",
            "recommendation": self.recommendation,
            "opened_at": self.opened_at,
            "review": None,
        }
        values.update(overrides)
        return GovernanceWorkflow(**values)

    def test_creates_valid_pending_workflow(self) -> None:
        workflow = self.build_workflow()

        self.assertEqual(workflow.workflow_id, "wf-001")
        self.assertEqual(workflow.recommendation, self.recommendation)
        self.assertEqual(workflow.opened_at, self.opened_at)
        self.assertIsNone(workflow.review)

    def test_new_workflow_derived_properties(self) -> None:
        workflow = self.build_workflow()

        self.assertEqual(workflow.material_id, "MAT-0044")
        self.assertEqual(
            workflow.material_id,
            self.recommendation.material_id,
        )
        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rejects_blank_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(workflow_id="")

    def test_rejects_whitespace_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(workflow_id="   ")

    def test_rejects_naive_opened_at(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(
                opened_at=datetime(2026, 8, 18, 10, 0, 0),
            )

    def test_rejects_invalid_recommendation_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(recommendation="not-a-recommendation")

    def test_is_immutable(self) -> None:
        workflow = self.build_workflow()

        with self.assertRaises(FrozenInstanceError):
            workflow.workflow_id = "wf-002"


if __name__ == "__main__":
    unittest.main()
