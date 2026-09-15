"""Testes da camada de avaliação pura de Ground Truth."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.ground_truth import (
    DecisionRecommendationGroundTruth,
    DecisionRecommendationGroundTruthDataset,
    LabelProvenance,
)
from agent_lab.ground_truth_evaluation import (
    DecisionRecommendationCaseEvaluation,
    DecisionRecommendationEvaluationReport,
    evaluate_decision_recommendation,
    evaluate_decision_recommendations,
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


def _make_case_evaluation(
    *,
    evaluation_case_id: str = "CASE-001",
    ground_truth_id: str = "GT-001",
    material_id: str = "MAT-001",
    expected_decision: GovernanceDecision = GovernanceDecision.APPROVE,
    predicted_decision: GovernanceDecision = GovernanceDecision.APPROVE,
) -> DecisionRecommendationCaseEvaluation:
    return DecisionRecommendationCaseEvaluation(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id=material_id,
        expected_decision=expected_decision,
        predicted_decision=predicted_decision,
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


class DecisionRecommendationEvaluationReportTests(unittest.TestCase):
    """Testes unitários para a entidade imutável DecisionRecommendationEvaluationReport."""

    def test_nominal_construction_and_fields(self) -> None:
        c1 = _make_case_evaluation(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        c2 = _make_case_evaluation(evaluation_case_id="CASE-002", ground_truth_id="GT-002")

        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c1, c2),
        )

        self.assertEqual(report.dataset_id, "DATASET-001")
        self.assertEqual(report.cases, (c1, c2))

    def test_dataset_id_normalized_with_strip(self) -> None:
        report = DecisionRecommendationEvaluationReport(
            dataset_id="  DATASET-001 \t\n",
            cases=(),
        )

        self.assertEqual(report.dataset_id, "DATASET-001")

    def test_dataset_id_rejects_empty_or_whitespace(self) -> None:
        invalid_values = ("", "   ", "\t\n")
        for val in invalid_values:
            with self.subTest(value=val):
                with self.assertRaises(ValueError):
                    DecisionRecommendationEvaluationReport(
                        dataset_id=val,
                        cases=(),
                    )

    def test_dataset_id_rejects_invalid_type(self) -> None:
        non_string_values = (123, None, True, ["DATASET-001"])
        for val in non_string_values:
            with self.subTest(value=val):
                with self.assertRaises(TypeError):
                    DecisionRecommendationEvaluationReport(
                        dataset_id=val,  # type: ignore[arg-type]
                        cases=(),
                    )

    def test_cases_must_be_tuple(self) -> None:
        c1 = _make_case_evaluation()
        invalid_containers = ([c1], "invalid", None, {c1})
        for container in invalid_containers:
            with self.subTest(container=type(container)):
                with self.assertRaises(TypeError):
                    DecisionRecommendationEvaluationReport(
                        dataset_id="DATASET-001",
                        cases=container,  # type: ignore[arg-type]
                    )

    def test_cases_items_must_be_decision_recommendation_case_evaluation(self) -> None:
        c1 = _make_case_evaluation()
        invalid_items = (
            (c1, "invalid_item"),
            (123,),
            (None,),
            (c1, _make_ground_truth()),
        )
        for items in invalid_items:
            with self.subTest(items=items):
                with self.assertRaises(TypeError):
                    DecisionRecommendationEvaluationReport(
                        dataset_id="DATASET-001",
                        cases=items,  # type: ignore[arg-type]
                    )

    def test_duplicate_evaluation_case_id_rejected(self) -> None:
        c1 = _make_case_evaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
        )
        c2 = _make_case_evaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-002",
            material_id="MAT-002",
        )

        with self.assertRaises(ValueError) as ctx:
            DecisionRecommendationEvaluationReport(
                dataset_id="DATASET-001",
                cases=(c1, c2),
            )

        self.assertIn("duplicate evaluation_case_id", str(ctx.exception))

    def test_canonical_ordering_by_composite_key(self) -> None:
        c3 = _make_case_evaluation(evaluation_case_id="CASE-003", ground_truth_id="GT-001")
        c1 = _make_case_evaluation(evaluation_case_id="CASE-001", ground_truth_id="GT-003")
        c2 = _make_case_evaluation(evaluation_case_id="CASE-002", ground_truth_id="GT-002")

        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c3, c1, c2),
        )

        self.assertEqual(report.cases, (c1, c2, c3))

    def test_immutability_frozen(self) -> None:
        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(),
        )

        with self.assertRaises(FrozenInstanceError):
            report.dataset_id = "NEW-ID"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            report.cases = ()  # type: ignore[misc]

    def test_slots_prevents_dict(self) -> None:
        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(),
        )

        self.assertFalse(hasattr(report, "__dict__"))

    def test_metrics_scenario_a_all_matches(self) -> None:
        c1 = _make_case_evaluation(
            evaluation_case_id="CASE-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )
        c2 = _make_case_evaluation(
            evaluation_case_id="CASE-002",
            expected_decision=GovernanceDecision.REVIEW,
            predicted_decision=GovernanceDecision.REVIEW,
        )
        c3 = _make_case_evaluation(
            evaluation_case_id="CASE-003",
            expected_decision=GovernanceDecision.REJECT,
            predicted_decision=GovernanceDecision.REJECT,
        )

        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c1, c2, c3),
        )

        self.assertEqual(report.total_cases, 3)
        self.assertEqual(report.matched_cases, 3)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertEqual(report.accuracy, 1.0)
        self.assertTrue(report.is_perfect_match)
        self.assertFalse(report.is_empty)
        self.assertEqual(report.matches, (c1, c2, c3))
        self.assertEqual(report.mismatches, ())

    def test_metrics_scenario_b_mixed_matches_and_mismatches(self) -> None:
        c1 = _make_case_evaluation(
            evaluation_case_id="CASE-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.APPROVE,
        )
        c2 = _make_case_evaluation(
            evaluation_case_id="CASE-002",
            expected_decision=GovernanceDecision.REVIEW,
            predicted_decision=GovernanceDecision.REVIEW,
        )
        c3 = _make_case_evaluation(
            evaluation_case_id="CASE-003",
            expected_decision=GovernanceDecision.REJECT,
            predicted_decision=GovernanceDecision.REJECT,
        )
        c4 = _make_case_evaluation(
            evaluation_case_id="CASE-004",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.REVIEW,
        )

        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c1, c2, c3, c4),
        )

        self.assertEqual(report.total_cases, 4)
        self.assertEqual(report.matched_cases, 3)
        self.assertEqual(report.mismatched_cases, 1)
        self.assertEqual(report.accuracy, 0.75)
        self.assertFalse(report.is_perfect_match)
        self.assertFalse(report.is_empty)
        self.assertEqual(report.matches, (c1, c2, c3))
        self.assertEqual(report.mismatches, (c4,))

    def test_metrics_scenario_c_all_mismatches(self) -> None:
        c1 = _make_case_evaluation(
            evaluation_case_id="CASE-001",
            expected_decision=GovernanceDecision.APPROVE,
            predicted_decision=GovernanceDecision.REJECT,
        )
        c2 = _make_case_evaluation(
            evaluation_case_id="CASE-002",
            expected_decision=GovernanceDecision.REJECT,
            predicted_decision=GovernanceDecision.APPROVE,
        )

        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c1, c2),
        )

        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 2)
        self.assertEqual(report.accuracy, 0.0)
        self.assertFalse(report.is_perfect_match)
        self.assertFalse(report.is_empty)
        self.assertEqual(report.matches, ())
        self.assertEqual(report.mismatches, (c1, c2))

    def test_metrics_scenario_d_empty_dataset(self) -> None:
        report = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-EMPTY",
            cases=(),
        )

        self.assertEqual(report.total_cases, 0)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertIsNone(report.accuracy)
        self.assertTrue(report.is_empty)
        self.assertFalse(report.is_perfect_match)
        self.assertEqual(report.matches, ())
        self.assertEqual(report.mismatches, ())

    def test_metrics_scenario_e_order_independence(self) -> None:
        c1 = _make_case_evaluation(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        c2 = _make_case_evaluation(evaluation_case_id="CASE-002", ground_truth_id="GT-002")

        report_a = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c1, c2),
        )
        report_b = DecisionRecommendationEvaluationReport(
            dataset_id="DATASET-001",
            cases=(c2, c1),
        )

        self.assertEqual(report_a.cases, report_b.cases)


class EvaluateDecisionRecommendationsBatchTests(unittest.TestCase):
    """Testes unitários e defensivos para a função pura batch evaluate_decision_recommendations."""

    def test_batch_all_matches(self) -> None:
        gt1 = _make_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        gt2 = _make_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_recommendation=GovernanceDecision.REVIEW,
        )
        gt3 = _make_ground_truth(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-003",
            material_id="MAT-003",
            expected_recommendation=GovernanceDecision.REJECT,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-TEST-001",
            items=(gt1, gt2, gt3),
        )

        pred1 = _make_prediction(material_id="MAT-001", decision=GovernanceDecision.APPROVE)
        pred2 = _make_prediction(material_id="MAT-002", decision=GovernanceDecision.REVIEW)
        pred3 = _make_prediction(material_id="MAT-003", decision=GovernanceDecision.REJECT)

        predictions = {
            "CASE-001": pred1,
            "CASE-002": pred2,
            "CASE-003": pred3,
        }

        report = evaluate_decision_recommendations(dataset, predictions)

        self.assertIsInstance(report, DecisionRecommendationEvaluationReport)
        self.assertEqual(report.dataset_id, "DATASET-TEST-001")
        self.assertEqual(report.total_cases, 3)
        self.assertEqual(report.matched_cases, 3)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertEqual(report.accuracy, 1.0)
        self.assertTrue(report.is_perfect_match)
        self.assertFalse(report.is_empty)

    def test_batch_mixed_matches_and_mismatches(self) -> None:
        gt1 = _make_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        gt2 = _make_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_recommendation=GovernanceDecision.REVIEW,
        )
        gt3 = _make_ground_truth(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-003",
            material_id="MAT-003",
            expected_recommendation=GovernanceDecision.REJECT,
        )
        gt4 = _make_ground_truth(
            evaluation_case_id="CASE-004",
            ground_truth_id="GT-004",
            material_id="MAT-004",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-TEST-002",
            items=(gt1, gt2, gt3, gt4),
        )

        predictions = {
            "CASE-001": _make_prediction(material_id="MAT-001", decision=GovernanceDecision.APPROVE),
            "CASE-002": _make_prediction(material_id="MAT-002", decision=GovernanceDecision.REVIEW),
            "CASE-003": _make_prediction(material_id="MAT-003", decision=GovernanceDecision.REJECT),
            "CASE-004": _make_prediction(material_id="MAT-004", decision=GovernanceDecision.REVIEW),  # mismatch
        }

        report = evaluate_decision_recommendations(dataset, predictions)

        self.assertEqual(report.total_cases, 4)
        self.assertEqual(report.matched_cases, 3)
        self.assertEqual(report.mismatched_cases, 1)
        self.assertEqual(report.accuracy, 0.75)
        self.assertFalse(report.is_perfect_match)

    def test_batch_all_mismatches(self) -> None:
        gt1 = _make_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        gt2 = _make_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_recommendation=GovernanceDecision.REJECT,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-TEST-003",
            items=(gt1, gt2),
        )

        predictions = {
            "CASE-001": _make_prediction(material_id="MAT-001", decision=GovernanceDecision.REJECT),
            "CASE-002": _make_prediction(material_id="MAT-002", decision=GovernanceDecision.APPROVE),
        }

        report = evaluate_decision_recommendations(dataset, predictions)

        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 2)
        self.assertEqual(report.accuracy, 0.0)

    def test_batch_preserves_dataset_id(self) -> None:
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-ALPHA-CUSTOM-ID",
            items=(),
        )

        report = evaluate_decision_recommendations(dataset, {})

        self.assertEqual(report.dataset_id, "DATASET-ALPHA-CUSTOM-ID")

    def test_batch_returns_report_instance(self) -> None:
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-001",
            items=(),
        )

        report = evaluate_decision_recommendations(dataset, {})

        self.assertIsInstance(report, DecisionRecommendationEvaluationReport)

    def test_batch_order_independence_of_mapping_keys(self) -> None:
        gt1 = _make_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001", material_id="MAT-001")
        gt2 = _make_ground_truth(evaluation_case_id="CASE-002", ground_truth_id="GT-002", material_id="MAT-002")
        gt3 = _make_ground_truth(evaluation_case_id="CASE-003", ground_truth_id="GT-003", material_id="MAT-003")

        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-001",
            items=(gt3, gt1, gt2),
        )

        pred1 = _make_prediction(material_id="MAT-001")
        pred2 = _make_prediction(material_id="MAT-002")
        pred3 = _make_prediction(material_id="MAT-003")

        mapping_order_1 = {"CASE-001": pred1, "CASE-002": pred2, "CASE-003": pred3}
        mapping_order_2 = {"CASE-003": pred3, "CASE-001": pred1, "CASE-002": pred2}

        report_1 = evaluate_decision_recommendations(dataset, mapping_order_1)
        report_2 = evaluate_decision_recommendations(dataset, mapping_order_2)

        self.assertEqual(report_1.cases, report_2.cases)
        self.assertEqual(report_1.cases[0].evaluation_case_id, "CASE-001")
        self.assertEqual(report_1.cases[1].evaluation_case_id, "CASE-002")
        self.assertEqual(report_1.cases[2].evaluation_case_id, "CASE-003")

    def test_batch_same_material_id_in_multiple_evaluation_case_ids(self) -> None:
        """Prova que o pareamento metrológico é governado por evaluation_case_id e não por material_id."""
        shared_material_id = "MAT-SHARED-100"

        gt_clean = _make_ground_truth(
            evaluation_case_id="CASE-CLEAN-001",
            ground_truth_id="GT-CLEAN-001",
            material_id=shared_material_id,
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        gt_stress = _make_ground_truth(
            evaluation_case_id="CASE-STRESS-002",
            ground_truth_id="GT-STRESS-002",
            material_id=shared_material_id,
            expected_recommendation=GovernanceDecision.REJECT,
        )

        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DATASET-SHARED-MAT",
            items=(gt_clean, gt_stress),
        )

        pred_clean = _make_prediction(
            material_id=shared_material_id,
            decision=GovernanceDecision.APPROVE,
        )
        pred_stress = _make_prediction(
            material_id=shared_material_id,
            decision=GovernanceDecision.REJECT,
        )

        predictions = {
            "CASE-CLEAN-001": pred_clean,
            "CASE-STRESS-002": pred_stress,
        }

        report = evaluate_decision_recommendations(dataset, predictions)

        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 2)
        self.assertEqual(report.accuracy, 1.0)
        self.assertTrue(report.is_perfect_match)

        self.assertEqual(report.cases[0].evaluation_case_id, "CASE-CLEAN-001")
        self.assertEqual(report.cases[0].expected_decision, GovernanceDecision.APPROVE)
        self.assertEqual(report.cases[0].predicted_decision, GovernanceDecision.APPROVE)

        self.assertEqual(report.cases[1].evaluation_case_id, "CASE-STRESS-002")
        self.assertEqual(report.cases[1].expected_decision, GovernanceDecision.REJECT)
        self.assertEqual(report.cases[1].predicted_decision, GovernanceDecision.REJECT)

    def test_rejects_dataset_not_decision_recommendation_ground_truth_dataset(self) -> None:
        invalid_datasets = ("invalid", 123, None, [_make_ground_truth()])
        for ds in invalid_datasets:
            with self.subTest(dataset=type(ds)):
                with self.assertRaises(TypeError):
                    evaluate_decision_recommendations(ds, {})  # type: ignore[arg-type]

    def test_rejects_predictions_not_mapping(self) -> None:
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=())
        invalid_predictions = ([_make_prediction()], (_make_prediction(),), "invalid", 123, None)
        for pred in invalid_predictions:
            with self.subTest(predictions=type(pred)):
                with self.assertRaises(TypeError):
                    evaluate_decision_recommendations(dataset, pred)  # type: ignore[arg-type]

    def test_rejects_predictions_mapping_value_not_decision_recommendation(self) -> None:
        gt = _make_ground_truth(evaluation_case_id="CASE-001")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt,))

        invalid_mappings = (
            {"CASE-001": "invalid_prediction"},
            {"CASE-001": 123},
            {"CASE-001": None},
            {"CASE-001": gt},
        )
        for m in invalid_mappings:
            with self.subTest(mapping=m):
                with self.assertRaises(TypeError):
                    evaluate_decision_recommendations(dataset, m)  # type: ignore[arg-type]

    def test_rejects_predictions_key_not_string(self) -> None:
        gt = _make_ground_truth(evaluation_case_id="CASE-001")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt,))

        pred = _make_prediction()
        invalid_keyed_mappings = (
            {123: pred},
            {None: pred},
            {True: pred},
        )
        for m in invalid_keyed_mappings:
            with self.subTest(mapping=m):
                with self.assertRaises(TypeError):
                    evaluate_decision_recommendations(dataset, m)  # type: ignore[arg-type]

    def test_rejects_missing_key_in_predictions(self) -> None:
        gt1 = _make_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        gt2 = _make_ground_truth(evaluation_case_id="CASE-002", ground_truth_id="GT-002")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt1, gt2))

        predictions = {
            "CASE-001": _make_prediction(),
        }

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, predictions)

        self.assertIn("missing predictions", str(ctx.exception))
        self.assertIn("CASE-002", str(ctx.exception))

    def test_rejects_extra_key_in_predictions(self) -> None:
        gt1 = _make_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt1,))

        predictions = {
            "CASE-001": _make_prediction(),
            "CASE-EXTRA-999": _make_prediction(),
        }

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, predictions)

        self.assertIn("unexpected predictions", str(ctx.exception))
        self.assertIn("CASE-EXTRA-999", str(ctx.exception))

    def test_rejects_simultaneous_missing_and_extra_keys(self) -> None:
        gt1 = _make_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        gt2 = _make_ground_truth(evaluation_case_id="CASE-002", ground_truth_id="GT-002")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt1, gt2))

        predictions = {
            "CASE-001": _make_prediction(),
            "CASE-UNKNOWN": _make_prediction(),
        }

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, predictions)

        self.assertIn("missing predictions", str(ctx.exception))

    def test_rejects_material_id_mismatch_for_evaluation_case(self) -> None:
        gt1 = _make_ground_truth(evaluation_case_id="CASE-001", material_id="MAT-CORRECT")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt1,))

        predictions = {
            "CASE-001": _make_prediction(material_id="MAT-WRONG"),
        }

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, predictions)

        self.assertIn("material_id mismatch", str(ctx.exception))

    def test_empty_dataset_and_empty_mapping_produces_empty_report(self) -> None:
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DATASET-EMPTY", items=())

        report = evaluate_decision_recommendations(dataset, {})

        self.assertEqual(report.dataset_id, "DATASET-EMPTY")
        self.assertEqual(report.total_cases, 0)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertIsNone(report.accuracy)
        self.assertTrue(report.is_empty)
        self.assertFalse(report.is_perfect_match)
        self.assertEqual(report.cases, ())

    def test_rejects_empty_dataset_with_non_empty_mapping(self) -> None:
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DATASET-EMPTY", items=())
        predictions = {"CASE-001": _make_prediction()}

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, predictions)

        self.assertIn("unexpected predictions", str(ctx.exception))

    def test_rejects_non_empty_dataset_with_empty_mapping(self) -> None:
        gt = _make_ground_truth(evaluation_case_id="CASE-001")
        dataset = DecisionRecommendationGroundTruthDataset(dataset_id="DS-01", items=(gt,))

        with self.assertRaises(ValueError) as ctx:
            evaluate_decision_recommendations(dataset, {})

        self.assertIn("missing predictions", str(ctx.exception))


class GroundTruthEvaluationPublicExportsTests(unittest.TestCase):
    """Testes de disponibilidade dos símbolos canônicos na API pública raiz (agent_lab)."""

    def test_symbols_exported_at_root_package(self) -> None:
        import agent_lab

        expected_symbols = (
            "DecisionRecommendationCaseEvaluation",
            "DecisionRecommendationEvaluationReport",
            "evaluate_decision_recommendation",
            "evaluate_decision_recommendations",
        )
        for symbol_name in expected_symbols:
            with self.subTest(symbol=symbol_name):
                self.assertTrue(
                    hasattr(agent_lab, symbol_name),
                    f"Symbol {symbol_name} must be accessible directly from agent_lab",
                )

    def test_symbols_present_in_root_all(self) -> None:
        import agent_lab

        self.assertTrue(hasattr(agent_lab, "__all__"))
        root_all = getattr(agent_lab, "__all__")
        expected_symbols = (
            "DecisionRecommendationCaseEvaluation",
            "DecisionRecommendationEvaluationReport",
            "evaluate_decision_recommendation",
            "evaluate_decision_recommendations",
        )
        for symbol_name in expected_symbols:
            with self.subTest(symbol=symbol_name):
                self.assertIn(
                    symbol_name,
                    root_all,
                    f"Symbol {symbol_name} must be declared in agent_lab.__all__",
                )

    def test_symbols_can_be_imported_from_agent_lab(self) -> None:
        from agent_lab import (
            DecisionRecommendationCaseEvaluation as DirectCaseEval,
            DecisionRecommendationEvaluationReport as DirectReport,
            evaluate_decision_recommendation as direct_eval_one,
            evaluate_decision_recommendations as direct_eval_batch,
        )

        self.assertIs(DirectCaseEval, DecisionRecommendationCaseEvaluation)
        self.assertIs(DirectReport, DecisionRecommendationEvaluationReport)
        self.assertIs(direct_eval_one, evaluate_decision_recommendation)
        self.assertIs(direct_eval_batch, evaluate_decision_recommendations)


if __name__ == "__main__":
    unittest.main()
