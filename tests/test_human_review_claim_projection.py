from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
    project_human_review_claim_state,
)


class HumanReviewClaimProjectionSlice1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.other_claim = HumanReviewClaim(
            claim_id="CLM-999",
            workflow_id="WF-OTHER",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )

    def test_project_claim_state_with_empty_claims_returns_no_claim(self) -> None:
        result = project_human_review_claim_state("WF-001", ())

        self.assertIsInstance(result, HumanReviewClaimState)
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.claims, ())
        self.assertEqual(result.claim_count, 0)
        self.assertIs(result.state, HumanReviewClaimFactState.NO_CLAIM)
        self.assertTrue(result.is_unclaimed)
        self.assertFalse(result.has_claims)
        self.assertFalse(result.has_multiple_claims)
        self.assertIsNone(result.sole_claim)

    def test_project_claim_state_when_all_claims_belong_to_other_workflows_returns_no_claim(
        self,
    ) -> None:
        result = project_human_review_claim_state("WF-001", (self.other_claim,))

        self.assertIsInstance(result, HumanReviewClaimState)
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.claims, ())
        self.assertEqual(result.claim_count, 0)
        self.assertIs(result.state, HumanReviewClaimFactState.NO_CLAIM)
        self.assertTrue(result.is_unclaimed)
        self.assertFalse(result.has_claims)
        self.assertFalse(result.has_multiple_claims)
        self.assertIsNone(result.sole_claim)

    def test_read_model_derives_claim_count_and_state_and_rejects_them_as_constructor_fields(
        self,
    ) -> None:
        state = HumanReviewClaimState(workflow_id="WF-001", claims=())

        self.assertEqual(state.claim_count, 0)
        self.assertIs(state.state, HumanReviewClaimFactState.NO_CLAIM)

        with self.assertRaises(TypeError):
            HumanReviewClaimState(  # type: ignore[call-arg]
                workflow_id="WF-001",
                claims=(),
                claim_count=0,
            )

        with self.assertRaises(TypeError):
            HumanReviewClaimState(  # type: ignore[call-arg]
                workflow_id="WF-001",
                claims=(),
                state=HumanReviewClaimFactState.NO_CLAIM,
            )


if __name__ == "__main__":
    unittest.main()
