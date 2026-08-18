from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from agent_lab import workflow as workflow_module
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
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
        self.verified_at = datetime(
            2026,
            8,
            18,
            9,
            30,
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
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação APPROVE para teste.",
            requires_human_decision=True,
        )
        self.reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-12345",
            verified_at=self.verified_at,
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

    def build_review(self, **overrides) -> HumanReview:
        values = {
            "review_id": "rev-001",
            "material_id": "MAT-0044",
            "system_recommendation": GovernanceDecision.APPROVE,
            "human_decision": HumanDecision.APPROVE,
            "reviewer_identity": self.reviewer_identity,
            "reviewed_at": self.reviewed_at,
            "justification": None,
            "corrections": (),
        }
        values.update(overrides)
        return HumanReview(**values)

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

    def test_rejects_invalid_review_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(review="not-a-human-review")

    def test_rejects_review_with_different_material_id(self) -> None:
        review = self.build_review(material_id="MAT-OTHER")
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_rejects_review_with_different_system_recommendation(self) -> None:
        review = self.build_review(
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
        )
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_rejects_review_before_opened_at(self) -> None:
        earlier_reviewed_at = datetime(
            2026,
            8,
            18,
            9,
            45,
            0,
            tzinfo=timezone.utc,
        )
        earlier_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-12345",
            verified_at=datetime(2026, 8, 18, 9, 30, 0, tzinfo=timezone.utc),
        )
        review = self.build_review(
            reviewed_at=earlier_reviewed_at,
            reviewer_identity=earlier_identity,
        )
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_conclude_returns_new_workflow_and_leaves_original_unmodified(
        self,
    ) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertIsNot(concluded, original)
        self.assertIsNone(original.review)
        self.assertEqual(original.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(original.closed_at)
        self.assertIsNone(original.review_lead_time)

    def test_concluded_workflow_preserves_identifiers_and_sets_review_and_status(
        self,
    ) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertEqual(concluded.workflow_id, original.workflow_id)
        self.assertEqual(concluded.recommendation, original.recommendation)
        self.assertEqual(concluded.material_id, original.material_id)
        self.assertEqual(concluded.opened_at, original.opened_at)
        self.assertEqual(concluded.review, review)
        self.assertEqual(concluded.status, WorkflowStatus.REVIEWED)

    def test_concluded_workflow_derived_temporal_properties(self) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertEqual(concluded.closed_at, self.reviewed_at)
        expected_lead_time = self.reviewed_at - self.opened_at
        self.assertEqual(concluded.review_lead_time, expected_lead_time)
        self.assertEqual(concluded.review_lead_time, timedelta(minutes=45))

    def test_conclude_rejects_already_reviewed_workflow(self) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        second_review = self.build_review(review_id="rev-002")
        with self.assertRaises(ValueError):
            workflow_module.conclude_governance_workflow(
                concluded, second_review
            )


if __name__ == "__main__":
    unittest.main()
