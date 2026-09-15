"""Testes da camada de avaliação pura de Ground Truth (Slice A)."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.ground_truth import (
    DecisionRecommendationGroundTruth,
    LabelProvenance,
)
from agent_lab.ground_truth_evaluation import (
    DecisionRecommendationCaseEvaluation,
    evaluate_decision_recommendation,
)


def _make_ground_truth(
    *,
    evaluation_case_id: str = "CASE-001",
    ground_truth_id: str = "GT-001",
    material_id: str = "MAT-001",
    expected_recommendation: GovernanceDecision = GovernanceDecision.APPROVE,
) -> DecisionRecommendationGroundTruth:
    return DecisionRecommendationGroundTruth(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id=material_id,
        expected_recommendation=expected_recommendation,
        provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
        source_reference="synthetic://spec-0124/test",
        annotator=None,
        labeled_at=datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc),
        rationale="Referência de teste para avaliação.",
    )


def _make_prediction(
    *,
    material_id: str = "MAT-001",
    decision: GovernanceDecision = GovernanceDecision.APPROVE,
) -> DecisionRecommendation:
    return DecisionRecommendation(
        material_id=material_id,
        decision=decision,
        evidence=(),
        rationale="Predição de teste para avaliação.",
        requires_human_decision=True,
    )


class DecisionRecommendationCaseEvaluationTests(unittest.TestCase):
    """Testes unitários para a entidade imutável DecisionRecommendationCaseEvaluation."""

    def test_nominal_construction_and_fields(self) -> None:
        evaluation = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )

        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id, "MAT-001")
        self.assertEqual(evaluation.expected_decision, GovernanceDecision.APPROVE)
        self.assertEqual(evaluation.predicted_decision, GovernanceDecision.APPROVE)
        self.assertTrue(evaluation.is_match)
        self.assertFalse(evaluation.is_mismatch)

    def test_string_fields_normalized_with_strip(self) -> None:
        evaluation = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="  CASE-001  ",
            ground_truth_id="  GT-001\t",
            material_id="\nMAT-001  ",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )

        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id, "MAT-001")

    def test_string_fields_reject_empty_or_whitespace(self) -> None:
        invalid_values = ("", "   ", "\t\n")
        for val in invalid_values:
            with self.subTest(field="evaluation_case_id", value=val):
                with self.assertRaises(ValueError):
                    DecisionRecommendationCaseEvaluation(
                        evaluation_case_id=val,
                        ground_truth_id="GT-001",
                        material_id="MAT-001",
                        expected_decision=GovernanceDecision.APPROVE,
                        predicted_decision=GovernanceDecision.APPROVE,
                    )

            with self.subTest(field="ground_truth_id", value=val):
                with self.assertRaises(ValueError):
                    DecisionRecommendationCaseEvaluation(
                        evaluation_case_id="CASE-001",
                        ground_truth_id=val,
                        material_id="MAT-001",
                        expected_decision=GovernanceDecision.APPROVE,
                        predicted_decision=GovernanceDecision.APPROVE,
                    )

            with self.subTest(field="material_id", value=val):
                with self.assertRaises(ValueError):
                    DecisionRecommendationCaseEvaluation(
                        evaluation_case_id="CASE-001",
                        ground_truth_id="GT-001",
                        material_id=val,
                        expected_decision=GovernanceDecision.APPROVE,
                        predicted_decision=GovernanceDecision.APPROVE,
                    )

    def test_string_fields_reject_non_string_types(self) -> None:
        non_string_values = (123, None, True, ["CASE-001"])
        for val in non_string_values:
            with self.subTest(value=val):
                with self.assertRaises(TypeError):
                    DecisionRecommendationCaseEvaluation(
                        evaluation_case_id=val,  # type: ignore[arg-type]
                        ground_truth_id="GT-001",
                        material_id="MAT-001",
                        expected_decision=GovernanceDecision.APPROVE,
                        predicted_decision=GovernanceDecision.APPROVE,
                    )

    def test_expected_decision_must_be_governance_decision(self) -> None:
        with self.assertRaises(TypeError):
            DecisionRecommendationCaseEvaluation(
                evaluation_case_id="CASE-001",
                ground_truth_id="GT-001",
                material_id="MAT-001",
                expected_decision="APPROVE",  # type: ignore[arg-type]
                predicted_decision=GovernanceDecision.APPROVE,
            )

    def test_predicted_decision_must_be_governance_decision(self) -> None:
        with self.assertRaises(TypeError):
            DecisionRecommendationCaseEvaluation(
                evaluation_case_id="CASE-001",
                ground_truth_id="GT-001",
                material_id="MAT-001",
                expected_decision=GovernanceDecision.APPROVE,
                predicted_decision="APPROVE",  # type: ignore[arg-type]
            )

    def test_immutability_frozen(self) -> None:
        evaluation = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )

        with self.assertRaises(FrozenInstanceError):
            evaluation.predicted_decision = GovernanceDecision.REJECT  # type: ignore[misc]

    def test_slots_prevents_dict(self) -> None:
        evaluation = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )

        self.assertFalse(hasattr(evaluation, "__dict__"))

    def test_is_match_and_is_mismatch_properties(self) -> None:
        match_eval = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_decision=GovernanceDecision.REVIEW,
            predicted_decision=GovernanceDecision.REVIEW,
        )
        self.assertTrue(match_eval.is_match)
        self.assertFalse(match_eval.is_mismatch)

        mismatch_eval = DecisionRecommendationCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.REJECT,
        )
        self.assertFalse(mismatch_eval.is_match)
        self.assertTrue(mismatch_eval.is_mismatch)


class EvaluateDecisionRecommendationTests(unittest.TestCase):
    """Testes da função pura evaluate_decision_recommendation."""

    def test_match_approve_vs_approve(self) -> None:
        gt = _make_ground_truth(expected_recommendation=GovernanceDecision.APPROVE)
        pred = _make_prediction(decision=GovernanceDecision.APPROVE)

        result = evaluate_decision_recommendation(gt, pred)

        self.assertIsInstance(result, DecisionRecommendationCaseEvaluation)
        self.assertTrue(result.is_match)
        self.assertFalse(result.is_mismatch)
        self.assertEqual(result.expected_decision, GovernanceDecision.APPROVE)
        self.assertEqual(result.predicted_decision, GovernanceDecision.APPROVE)

    def test_match_review_vs_review(self) -> None:
        gt = _make_ground_truth(expected_recommendation=GovernanceDecision.REVIEW)
        pred = _make_prediction(decision=GovernanceDecision.REVIEW)

        result = evaluate_decision_recommendation(gt, pred)

        self.assertTrue(result.is_match)
        self.assertFalse(result.is_mismatch)
        self.assertEqual(result.expected_decision, GovernanceDecision.REVIEW)
        self.assertEqual(result.predicted_decision, GovernanceDecision.REVIEW)

    def test_match_reject_vs_reject(self) -> None:
        gt = _make_ground_truth(expected_recommendation=GovernanceDecision.REJECT)
        pred = _make_prediction(decision=GovernanceDecision.REJECT)

        result = evaluate_decision_recommendation(gt, pred)

        self.assertTrue(result.is_match)
        self.assertFalse(result.is_mismatch)
        self.assertEqual(result.expected_decision, GovernanceDecision.REJECT)
        self.assertEqual(result.predicted_decision, GovernanceDecision.REJECT)

    def test_mismatch_review_vs_approve(self) -> None:
        gt = _make_ground_truth(expected_recommendation=GovernanceDecision.APPROVE)
        pred = _make_prediction(decision=GovernanceDecision.REVIEW)

        result = evaluate_decision_recommendation(gt, pred)

        self.assertFalse(result.is_match)
        self.assertTrue(result.is_mismatch)
        self.assertEqual(result.expected_decision, GovernanceDecision.APPROVE)
        self.assertEqual(result.predicted_decision, GovernanceDecision.REVIEW)

    def test_mismatch_reject_vs_review(self) -> None:
        gt = _make_ground_truth(expected_recommendation=GovernanceDecision.REVIEW)
        pred = _make_prediction(decision=GovernanceDecision.REJECT)

        result = evaluate_decision_recommendation(gt, pred)

        self.assertFalse(result.is_match)
        self.assertTrue(result.is_mismatch)
        self.assertEqual(result.expected_decision, GovernanceDecision.REVIEW)
        self.assertEqual(result.predicted_decision, GovernanceDecision.REJECT)

    def test_returned_fields_preserve_identities(self) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-X-999",
            ground_truth_id="GT-Y-888",
            material_id="MAT-Z-777",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        pred = _make_prediction(
            material_id="MAT-Z-777",
            decision=GovernanceDecision.APPROVE,
        )

        result = evaluate_decision_recommendation(gt, pred)

        self.assertEqual(result.evaluation_case_id, "CASE-X-999")
        self.assertEqual(result.ground_truth_id, "GT-Y-888")
        self.assertEqual(result.material_id, "MAT-Z-777")
        self.assertEqual(result.expected_decision, GovernanceDecision.APPROVE)
        self.assertEqual(result.predicted_decision, GovernanceDecision.APPROVE)

    def test_rejects_invalid_ground_truth_type(self) -> None:
        pred = _make_prediction()

        with self.assertRaises(TypeError):
            evaluate_decision_recommendation(
                "invalid_ground_truth",  # type: ignore[arg-type]
                pred,
            )

    def test_rejects_invalid_prediction_type(self) -> None:
        gt = _make_ground_truth()

        with self.assertRaises(TypeError):
            evaluate_decision_recommendation(
                gt,
                "invalid_prediction",  # type: ignore[arg-type]
            )

    def test_rejects_material_id_mismatch(self) -> None:
        gt = _make_ground_truth(material_id="MAT-001")
        pred = _make_prediction(material_id="MAT-002")

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendation(gt, pred)

        self.assertIn("material_id mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
