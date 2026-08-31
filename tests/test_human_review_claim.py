from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    claim_pending_human_review,
)
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class HumanReviewClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            31,
            9,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            31,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.claimed_at = datetime(
            2026,
            8,
            31,
            9,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0001",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação de teste",
            requires_human_decision=True,
        )
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="corp-idp",
            identity_subject="specialist@corp.local",
            verification_id="ver-12345",
            verified_at=self.verified_at,
        )
        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )

    def test_claim_pending_human_review_success(self) -> None:
        claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLAIM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

        self.assertIsInstance(claim, HumanReviewClaim)
        self.assertEqual(claim.claim_id, "CLAIM-001")
        self.assertEqual(claim.workflow_id, self.workflow.workflow_id)
        self.assertEqual(claim.specialist, self.specialist)
        self.assertEqual(claim.claimed_at, self.claimed_at)
        self.assertEqual(
            self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(self.workflow.review)

    def test_claim_rejects_empty_claim_id(self) -> None:
        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_claim_rejects_whitespace_claim_id(self) -> None:
        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="   ",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_empty_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_invalid_specialist_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist="invalid-specialist",  # type: ignore[arg-type]
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_invalid_claimed_at_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=self.specialist,
                claimed_at="invalid-datetime",  # type: ignore[arg-type]
            )

    def test_human_review_claim_rejects_naive_claimed_at(self) -> None:
        naive_claimed_at = datetime(
            2026,
            8,
            31,
            9,
            15,
            0,
        )

        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=self.specialist,
                claimed_at=naive_claimed_at,
            )

    def test_human_review_claim_rejects_specialist_verified_after_claim(
        self,
    ) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-002",
            identity_provider="corp-idp",
            identity_subject="late@corp.local",
            verification_id="ver-late",
            verified_at=datetime(
                2026,
                8,
                31,
                9,
                30,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_allows_specialist_verified_at_claimed_at(
        self,
    ) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-003",
            identity_provider="corp-idp",
            identity_subject="boundary@corp.local",
            verification_id="ver-boundary",
            verified_at=self.claimed_at,
        )

        claim = HumanReviewClaim(
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            specialist=specialist,
            claimed_at=self.claimed_at,
        )

        self.assertEqual(claim.specialist, specialist)
        self.assertEqual(claim.claimed_at, self.claimed_at)

    def test_claim_rejects_claimed_at_before_opened_at(self) -> None:
        claimed_at = datetime(
            2026,
            8,
            31,
            8,
            45,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="CLAIM-001",
                specialist=self.specialist,
                claimed_at=claimed_at,
            )

    def test_claim_allows_claimed_at_equal_to_opened_at(self) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-004",
            identity_provider="corp-idp",
            identity_subject="opening-boundary@corp.local",
            verification_id="ver-opening-boundary",
            verified_at=self.workflow.opened_at,
        )

        claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLAIM-001",
            specialist=specialist,
            claimed_at=self.workflow.opened_at,
        )

        self.assertEqual(claim.claimed_at, self.workflow.opened_at)
        self.assertEqual(claim.workflow_id, self.workflow.workflow_id)


if __name__ == "__main__":
    unittest.main()
