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


class HumanReviewClaimProjectionSlice2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.claim = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )

    def test_project_claim_state_with_single_claim_returns_single_claim_state(
        self,
    ) -> None:
        result = project_human_review_claim_state("WF-001", (self.claim,))

        self.assertIsInstance(result, HumanReviewClaimState)
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.claims, (self.claim,))
        self.assertEqual(result.claim_count, 1)
        self.assertIs(result.state, HumanReviewClaimFactState.SINGLE_CLAIM)
        self.assertFalse(result.is_unclaimed)
        self.assertTrue(result.has_claims)
        self.assertFalse(result.has_multiple_claims)
        self.assertIs(result.sole_claim, self.claim)

    def test_read_model_derives_single_claim_state_from_cardinality(
        self,
    ) -> None:
        state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(self.claim,),
        )

        self.assertEqual(state.claim_count, 1)
        self.assertIs(state.state, HumanReviewClaimFactState.SINGLE_CLAIM)
        self.assertFalse(state.is_unclaimed)
        self.assertTrue(state.has_claims)
        self.assertFalse(state.has_multiple_claims)
        self.assertIs(state.sole_claim, self.claim)


class HumanReviewClaimProjectionSlice3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist1@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-002",
            identity_provider="CORP_IDP",
            identity_subject="specialist2@corp.local",
            verification_id="VER-002",
            verified_at=datetime(2026, 9, 2, 9, 5, 0, tzinfo=timezone.utc),
        )
        self.claim_wf1_a = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )
        self.claim_wf1_b = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc),
        )
        self.claim_wf2 = HumanReviewClaim(
            claim_id="CLM-003",
            workflow_id="WF-002",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 2, 9, 20, 0, tzinfo=timezone.utc),
        )

    def test_project_claim_state_with_two_claims_returns_multiple_claims_state(
        self,
    ) -> None:
        result = project_human_review_claim_state(
            "WF-001", (self.claim_wf1_a, self.claim_wf1_b)
        )

        self.assertIsInstance(result, HumanReviewClaimState)
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(len(result.claims), 2)
        self.assertEqual(set(result.claims), {self.claim_wf1_a, self.claim_wf1_b})
        self.assertEqual(result.claim_count, 2)
        self.assertIs(result.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertFalse(result.is_unclaimed)
        self.assertTrue(result.has_claims)
        self.assertTrue(result.has_multiple_claims)
        self.assertIsNone(result.sole_claim)

    def test_read_model_derives_multiple_claims_state_from_cardinality(
        self,
    ) -> None:
        state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(self.claim_wf1_a, self.claim_wf1_b),
        )

        self.assertEqual(state.claim_count, 2)
        self.assertIs(state.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertFalse(state.is_unclaimed)
        self.assertTrue(state.has_claims)
        self.assertTrue(state.has_multiple_claims)
        self.assertIsNone(state.sole_claim)

    def test_project_claim_state_filters_only_target_workflow_from_global_collection(
        self,
    ) -> None:
        global_claims = (self.claim_wf1_a, self.claim_wf2, self.claim_wf1_b)
        result = project_human_review_claim_state("WF-001", global_claims)

        self.assertIsInstance(result, HumanReviewClaimState)
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(len(result.claims), 2)
        self.assertEqual(set(result.claims), {self.claim_wf1_a, self.claim_wf1_b})
        self.assertNotIn(self.claim_wf2, result.claims)
        self.assertEqual(result.claim_count, 2)
        self.assertIs(result.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertFalse(result.is_unclaimed)
        self.assertTrue(result.has_claims)
        self.assertTrue(result.has_multiple_claims)
        self.assertIsNone(result.sole_claim)


if __name__ == "__main__":
    unittest.main()
