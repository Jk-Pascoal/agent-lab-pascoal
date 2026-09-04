from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimState,
    project_human_review_claim_state,
)
from agent_lab.pending_human_reviews_with_claim_state_use_case import (
    PendingHumanReviewWithClaimStateItem,
)
from agent_lab.workflow import GovernanceWorkflow


class PendingHumanReviewWithClaimStateItemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Recomendação REVIEW",
            requires_human_decision=True,
        )
        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_state = project_human_review_claim_state("WF-001", ())

    def test_valid_construction_preserves_attributes(self) -> None:
        item = PendingHumanReviewWithClaimStateItem(
            workflow=self.workflow,
            claim_state=self.claim_state,
        )

        self.assertIs(item.workflow, self.workflow)
        self.assertIs(item.claim_state, self.claim_state)
        self.assertEqual(item.workflow.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.workflow_id, "WF-001")

    def test_rejects_invalid_workflow_type(self) -> None:
        invalid_workflows = [
            "not-a-workflow",
            None,
            True,
            123,
            {"workflow_id": "WF-001"},
        ]
        for invalid in invalid_workflows:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    PendingHumanReviewWithClaimStateItem(
                        workflow=invalid,  # type: ignore[arg-type]
                        claim_state=self.claim_state,
                    )

    def test_rejects_invalid_claim_state_type(self) -> None:
        invalid_claim_states = [
            "not-a-claim-state",
            None,
            True,
            123,
            (),
        ]
        for invalid in invalid_claim_states:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    PendingHumanReviewWithClaimStateItem(
                        workflow=self.workflow,
                        claim_state=invalid,  # type: ignore[arg-type]
                    )

    def test_rejects_relational_mismatch_of_workflow_id(self) -> None:
        mismatched_claim_state = project_human_review_claim_state("WF-OTHER", ())

        with self.assertRaises(ValueError) as ctx:
            PendingHumanReviewWithClaimStateItem(
                workflow=self.workflow,
                claim_state=mismatched_claim_state,
            )

        self.assertIn("WF-001", str(ctx.exception))
        self.assertIn("WF-OTHER", str(ctx.exception))

    def test_item_is_immutable(self) -> None:
        item = PendingHumanReviewWithClaimStateItem(
            workflow=self.workflow,
            claim_state=self.claim_state,
        )

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.workflow = self.workflow  # type: ignore[misc]

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.claim_state = self.claim_state  # type: ignore[misc]
