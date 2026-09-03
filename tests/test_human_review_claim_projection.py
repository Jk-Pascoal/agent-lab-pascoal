from __future__ import annotations

from dataclasses import FrozenInstanceError
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


class HumanReviewClaimProjectionSlice4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_a = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 10, 0, tzinfo=timezone.utc),
        )
        self.claim_b = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 20, 0, tzinfo=timezone.utc),
        )
        self.claim_c = HumanReviewClaim(
            claim_id="CLM-003",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc),
        )

        self.claim_tie_1 = HumanReviewClaim(
            claim_id="CLM-010",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_tie_2 = HumanReviewClaim(
            claim_id="CLM-020",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
        )

        self.claim_other = HumanReviewClaim(
            claim_id="CLM-999",
            workflow_id="WF-OTHER",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )

    def test_canonical_sorting_independent_of_input_order(self) -> None:
        expected_canonical = (self.claim_a, self.claim_b, self.claim_c)

        projection_a = project_human_review_claim_state(
            "WF-001",
            (self.claim_c, self.claim_a, self.claim_b),
        )
        projection_b = project_human_review_claim_state(
            "WF-001",
            (self.claim_b, self.claim_c, self.claim_a),
        )

        self.assertEqual(projection_a, projection_b)
        self.assertEqual(projection_a.claims, expected_canonical)
        self.assertEqual(projection_b.claims, expected_canonical)

    def test_tie_break_lexicographically_by_claim_id_when_claimed_at_identical(
        self,
    ) -> None:
        expected_canonical = (self.claim_tie_1, self.claim_tie_2)

        # Fornecidos deliberadamente em ordem inversa (CLM-020 antes de CLM-010)
        projection = project_human_review_claim_state(
            "WF-001",
            (self.claim_tie_2, self.claim_tie_1),
        )

        self.assertEqual(projection.claims, expected_canonical)

    def test_canonical_sorting_with_interleaved_global_collection(self) -> None:
        expected_canonical = (self.claim_a, self.claim_b, self.claim_c)

        projection_1 = project_human_review_claim_state(
            "WF-001",
            (self.claim_other, self.claim_c, self.claim_a, self.claim_b),
        )
        projection_2 = project_human_review_claim_state(
            "WF-001",
            (self.claim_b, self.claim_other, self.claim_c, self.claim_a),
        )

        self.assertEqual(projection_1, projection_2)
        self.assertEqual(projection_1.claims, expected_canonical)
        self.assertEqual(projection_2.claims, expected_canonical)
        self.assertNotIn(self.claim_other, projection_1.claims)
        self.assertNotIn(self.claim_other, projection_2.claims)


class HumanReviewClaimProjectionSlice5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_target = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 10, 0, tzinfo=timezone.utc),
        )
        self.claim_other = HumanReviewClaim(
            claim_id="CLM-999",
            workflow_id="WF-OTHER",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )

    def test_project_claim_state_rejects_invalid_workflow_id_types_and_values(
        self,
    ) -> None:
        invalid_types = [None, 123, True, 45.6, ["WF-001"]]
        for invalid_wf in invalid_types:
            with self.subTest(invalid_type=type(invalid_wf)):
                with self.assertRaises(TypeError):
                    project_human_review_claim_state(invalid_wf, ())  # type: ignore[arg-type]

        invalid_values = ["", "   ", "\t\n"]
        for empty_wf in invalid_values:
            with self.subTest(empty_wf=empty_wf):
                with self.assertRaises(ValueError):
                    project_human_review_claim_state(empty_wf, ())

    def test_project_claim_state_sanitizes_workflow_id(self) -> None:
        result = project_human_review_claim_state(
            "  WF-001  ",
            (self.claim_target,),
        )

        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.claims, (self.claim_target,))
        self.assertEqual(result.claim_count, 1)

    def test_project_claim_state_rejects_non_sequence_claims_and_textual_binary_sequences(
        self,
    ) -> None:
        non_sequences = [
            None,
            123,
            True,
            {"claim": self.claim_target},
            {self.claim_target},
            (c for c in [self.claim_target]),
        ]
        for non_seq in non_sequences:
            with self.subTest(non_seq=type(non_seq)):
                with self.assertRaises(TypeError):
                    project_human_review_claim_state("WF-001", non_seq)  # type: ignore[arg-type]

        textual_or_binary_sequences = [
            "CLM-001",
            b"CLM-001",
            bytearray(b"CLM-001"),
        ]
        for textual_or_binary in textual_or_binary_sequences:
            with self.subTest(textual_or_binary=type(textual_or_binary)):
                with self.assertRaises(TypeError):
                    project_human_review_claim_state("WF-001", textual_or_binary)  # type: ignore[arg-type]

    def test_project_claim_state_validates_all_elements_fail_closed_before_filtering(
        self,
    ) -> None:
        # Coleção com claim válido do workflow alvo, claim de outro workflow e elemento inválido (None)
        invalid_collection = (
            self.claim_target,
            None,
            self.claim_other,
        )
        with self.assertRaises(TypeError):
            project_human_review_claim_state("WF-001", invalid_collection)  # type: ignore[arg-type]

        # Elemento inválido no início da sequência
        invalid_at_start = (
            "not-a-claim",
            self.claim_target,
        )
        with self.assertRaises(TypeError):
            project_human_review_claim_state("WF-001", invalid_at_start)  # type: ignore[arg-type]

        # Elemento inválido no final da sequência pertencente apenas a outro workflow
        invalid_at_end = (
            self.claim_other,
            12345,
        )
        with self.assertRaises(TypeError):
            project_human_review_claim_state("WF-001", invalid_at_end)  # type: ignore[arg-type]

    def test_read_model_constructor_enforces_defensive_invariants(self) -> None:
        # Rejeitar claims que não seja tuple
        with self.assertRaises(TypeError):
            HumanReviewClaimState(
                workflow_id="WF-001",
                claims=[self.claim_target],  # type: ignore[arg-type]
            )

        # Rejeitar claims contendo elemento que não seja HumanReviewClaim
        with self.assertRaises(TypeError):
            HumanReviewClaimState(
                workflow_id="WF-001",
                claims=(self.claim_target, None),  # type: ignore[arg-type]
            )

        with self.assertRaises(TypeError):
            HumanReviewClaimState(
                workflow_id="WF-001",
                claims=(self.claim_target, True),  # type: ignore[arg-type]
            )

        # Rejeitar claim cujo workflow_id difira do workflow_id do read-model
        with self.assertRaises(ValueError):
            HumanReviewClaimState(
                workflow_id="WF-001",
                claims=(self.claim_other,),
            )

        # Rejeitar workflow_id inválido
        for invalid_wf in [None, 123, True]:
            with self.subTest(invalid_wf=type(invalid_wf)):
                with self.assertRaises(TypeError):
                    HumanReviewClaimState(
                        workflow_id=invalid_wf,  # type: ignore[arg-type]
                        claims=(),
                    )

        for empty_wf in ["", "   "]:
            with self.subTest(empty_wf=empty_wf):
                with self.assertRaises(ValueError):
                    HumanReviewClaimState(
                        workflow_id=empty_wf,
                        claims=(),
                    )

        # Sanitização do workflow_id no construtor
        state = HumanReviewClaimState(
            workflow_id="  WF-001  ",
            claims=(),
        )
        self.assertEqual(state.workflow_id, "WF-001")

    def test_read_model_enforces_immutability(self) -> None:
        state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(self.claim_target,),
        )

        with self.assertRaises(FrozenInstanceError):
            state.workflow_id = "WF-002"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            state.claims = ()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
