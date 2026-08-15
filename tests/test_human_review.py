import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
)


class CorrectionRequestTests(unittest.TestCase):
    def test_creates_valid_correction_request(self):
        correction = CorrectionRequest(
            field_name="unit_of_measure",
            reason="Unidade fora do padrão corporativo.",
            suggested_value="PC",
        )

        self.assertEqual(correction.field_name, "unit_of_measure")
        self.assertEqual(
            correction.reason,
            "Unidade fora do padrão corporativo.",
        )
        self.assertEqual(correction.suggested_value, "PC")

    def test_suggested_value_is_optional(self):
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição ambígua.",
        )

        self.assertIsNone(correction.suggested_value)

    def test_rejects_blank_field_name(self):
        with self.assertRaises(ValueError):
            CorrectionRequest(
                field_name="   ",
                reason="Campo obrigatório.",
            )

    def test_rejects_blank_reason(self):
        with self.assertRaises(ValueError):
            CorrectionRequest(
                field_name="unit_of_measure",
                reason="   ",
            )

    def test_is_immutable(self):
        correction = CorrectionRequest(
            field_name="unit_of_measure",
            reason="Unidade fora do padrão.",
        )

        with self.assertRaises(FrozenInstanceError):
            correction.reason = "Motivo alterado."


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.reviewed_at = datetime(
            2026,
            8,
            15,
            13,
            0,
            tzinfo=timezone.utc,
        )
        self.correction = CorrectionRequest(
            field_name="unit_of_measure",
            reason="Padronizar a unidade de medida.",
            suggested_value="PC",
        )

    def build_review(self, **overrides):
        values = {
            "review_id": "review-001",
            "material_id": "MAT-001",
            "system_recommendation": GovernanceDecision.REVIEW,
            "human_decision": HumanDecision.REQUEST_CORRECTION,
            "reviewer_id": "specialist-001",
            "reviewed_at": self.reviewed_at,
            "justification": "Unidade de medida precisa ser corrigida.",
            "corrections": (self.correction,),
        }
        values.update(overrides)
        return HumanReview(**values)

    def test_creates_valid_human_review(self):
        review = self.build_review()

        self.assertEqual(review.review_id, "review-001")
        self.assertEqual(review.material_id, "MAT-001")
        self.assertEqual(
            review.system_recommendation,
            GovernanceDecision.REVIEW,
        )
        self.assertEqual(
            review.human_decision,
            HumanDecision.REQUEST_CORRECTION,
        )
        self.assertEqual(review.reviewer_id, "specialist-001")
        self.assertEqual(review.reviewed_at, self.reviewed_at)
        self.assertEqual(review.corrections, (self.correction,))

    def test_approve_agrees_with_approve_recommendation(self):
        review = self.build_review(
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            justification=None,
            corrections=(),
        )

        self.assertTrue(review.agrees_with_system)

    def test_reject_agrees_with_reject_recommendation(self):
        review = self.build_review(
            system_recommendation=GovernanceDecision.REJECT,
            human_decision=HumanDecision.REJECT,
            justification="Material viola regra crítica.",
            corrections=(),
        )

        self.assertTrue(review.agrees_with_system)

    def test_request_correction_agrees_with_review_recommendation(self):
        review = self.build_review()

        self.assertTrue(review.agrees_with_system)

    def test_records_divergence_without_changing_recommendation(self):
        review = self.build_review(
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.REJECT,
            justification="Especialista encontrou conflito de classificação.",
            corrections=(),
        )

        self.assertFalse(review.agrees_with_system)
        self.assertEqual(
            review.system_recommendation,
            GovernanceDecision.APPROVE,
        )

    def test_rejects_blank_review_id(self):
        with self.assertRaises(ValueError):
            self.build_review(review_id="   ")

    def test_rejects_blank_material_id(self):
        with self.assertRaises(ValueError):
            self.build_review(material_id="   ")

    def test_rejects_blank_reviewer_id(self):
        with self.assertRaises(ValueError):
            self.build_review(reviewer_id="   ")

    def test_rejects_naive_timestamp(self):
        with self.assertRaises(ValueError):
            self.build_review(
                reviewed_at=datetime(2026, 8, 15, 13, 0),
            )

    def test_reject_requires_justification(self):
        with self.assertRaises(ValueError):
            self.build_review(
                human_decision=HumanDecision.REJECT,
                justification="   ",
                corrections=(),
            )

    def test_request_correction_requires_justification(self):
        with self.assertRaises(ValueError):
            self.build_review(justification="   ")

    def test_request_correction_requires_at_least_one_correction(self):
        with self.assertRaises(ValueError):
            self.build_review(corrections=())

    def test_approve_rejects_corrections(self):
        with self.assertRaises(ValueError):
            self.build_review(
                system_recommendation=GovernanceDecision.APPROVE,
                human_decision=HumanDecision.APPROVE,
                justification=None,
                corrections=(self.correction,),
            )

    def test_converts_corrections_to_immutable_tuple(self):
        source = [self.correction]

        review = self.build_review(corrections=source)
        source.clear()

        self.assertEqual(review.corrections, (self.correction,))
        self.assertIsInstance(review.corrections, tuple)

    def test_is_immutable(self):
        review = self.build_review()

        with self.assertRaises(FrozenInstanceError):
            review.reviewer_id = "specialist-002"


if __name__ == "__main__":
    unittest.main()

