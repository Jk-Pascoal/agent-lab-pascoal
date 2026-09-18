"""Testes da camada de avaliação pura de Ground Truth."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueType
from agent_lab.ground_truth import (
    DecisionRecommendationGroundTruth,
    DecisionRecommendationGroundTruthDataset,
    DuplicatePairGroundTruth,
    LabelProvenance,
    MaterialRuleGroundTruth,
    MaterialRuleGroundTruthDataset,
)
from agent_lab.ground_truth_evaluation import (
    DecisionRecommendationCaseEvaluation,
    DecisionRecommendationEvaluationReport,
    DuplicatePairCaseEvaluation,
    DuplicatePairPrediction,
    MaterialRuleCaseEvaluation,
    MaterialRuleEvaluationReport,
    MaterialRulePrediction,
    evaluate_decision_recommendation,
    evaluate_decision_recommendations,
    evaluate_duplicate_pair,
    evaluate_material_rule,
    evaluate_material_rules,
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


def _make_rule_ground_truth(
    *,
    evaluation_case_id: str = "CASE-001",
    ground_truth_id: str = "GT-001",
    material_id: str = "MAT-001",
    expected_issue_types: tuple[IssueType, ...] = (IssueType.INVALID_UNIT,),
) -> MaterialRuleGroundTruth:
    return MaterialRuleGroundTruth(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id=material_id,
        expected_issue_types=expected_issue_types,
        provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
        source_reference="synthetic://spec-0129/test",
        annotator=None,
        labeled_at=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
        rationale="Referência de teste para avaliação de regras.",
    )


def _make_rule_prediction(
    *,
    material_id: str = "MAT-001",
    predicted_issue_types: tuple[IssueType, ...] = (IssueType.INVALID_UNIT,),
) -> MaterialRulePrediction:
    return MaterialRulePrediction(
        material_id=material_id,
        predicted_issue_types=predicted_issue_types,
    )


def _make_duplicate_pair_ground_truth(
    *,
    evaluation_case_id: str = "CASE-001",
    ground_truth_id: str = "GT-001",
    material_id_a: str = "MAT-001",
    material_id_b: str = "MAT-002",
    is_duplicate: bool = True,
) -> DuplicatePairGroundTruth:
    return DuplicatePairGroundTruth(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id_a=material_id_a,
        material_id_b=material_id_b,
        is_duplicate=is_duplicate,
        provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
        source_reference="synthetic://spec-0133/test",
        annotator=None,
        labeled_at=datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc),
        rationale="Referência de teste para avaliação de par de duplicata.",
    )


def _make_duplicate_pair_prediction(
    *,
    material_id_a: str = "MAT-001",
    material_id_b: str = "MAT-002",
    is_duplicate: bool = True,
) -> DuplicatePairPrediction:
    return DuplicatePairPrediction(
        material_id_a=material_id_a,
        material_id_b=material_id_b,
        is_duplicate=is_duplicate,
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


class MaterialRulePredictionTests(unittest.TestCase):
    """Testes unitários defensivos para o contrato MaterialRulePrediction."""

    def test_valid_creation_and_fields(self) -> None:
        pred = MaterialRulePrediction(
            material_id="MAT-001",
            predicted_issue_types=(IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD),
        )
        self.assertEqual(pred.material_id, "MAT-001")
        self.assertEqual(
            pred.predicted_issue_types,
            (IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD),
        )

    def test_valid_creation_empty_issues(self) -> None:
        pred = MaterialRulePrediction(
            material_id="MAT-001",
            predicted_issue_types=(),
        )
        self.assertEqual(pred.material_id, "MAT-001")
        self.assertEqual(pred.predicted_issue_types, ())

    def test_trim_material_id(self) -> None:
        pred = MaterialRulePrediction(
            material_id="  MAT-001 \t ",
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        self.assertEqual(pred.material_id, "MAT-001")

    def test_material_id_invalid_types(self) -> None:
        invalid_types = (None, 123, False, True, [], {}, 4.5)
        for val in invalid_types:
            with self.subTest(value=val):
                with self.assertRaises(TypeError):
                    MaterialRulePrediction(
                        material_id=val,  # type: ignore[arg-type]
                        predicted_issue_types=(),
                    )

    def test_material_id_empty_or_whitespace(self) -> None:
        invalid_values = ("", "   ", "\t\n")
        for val in invalid_values:
            with self.subTest(value=val):
                with self.assertRaises(ValueError):
                    MaterialRulePrediction(
                        material_id=val,
                        predicted_issue_types=(),
                    )

    def test_predicted_issue_types_not_tuple(self) -> None:
        invalid_containers = (
            [IssueType.INVALID_UNIT],
            {IssueType.INVALID_UNIT},
            "INVALID_UNIT",
            None,
            123,
        )
        for val in invalid_containers:
            with self.subTest(container=type(val).__name__):
                with self.assertRaises(TypeError):
                    MaterialRulePrediction(
                        material_id="MAT-001",
                        predicted_issue_types=val,  # type: ignore[arg-type]
                    )

    def test_item_not_issue_type(self) -> None:
        invalid_items = (
            ("INVALID_UNIT",),
            (123,),
            (None,),
            (IssueType.INVALID_UNIT, "MISSING_CRITICAL_FIELD"),
        )
        for items in invalid_items:
            with self.subTest(items=items):
                with self.assertRaises(TypeError):
                    MaterialRulePrediction(
                        material_id="MAT-001",
                        predicted_issue_types=items,  # type: ignore[arg-type]
                    )

    def test_possible_duplicate_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MaterialRulePrediction(
                material_id="MAT-001",
                predicted_issue_types=(IssueType.POSSIBLE_DUPLICATE,),
            )
        self.assertIn("POSSIBLE_DUPLICATE is not permitted", str(ctx.exception))

    def test_duplicates_rejected_fail_closed(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MaterialRulePrediction(
                material_id="MAT-001",
                predicted_issue_types=(
                    IssueType.INVALID_UNIT,
                    IssueType.INVALID_UNIT,
                ),
            )
        self.assertIn("must not contain duplicates", str(ctx.exception))

    def test_canonicalization_of_order(self) -> None:
        pred = MaterialRulePrediction(
            material_id="MAT-001",
            predicted_issue_types=(
                IssueType.MISSING_TECHNICAL_ATTRIBUTE,
                IssueType.INVALID_UNIT,
                IssueType.AMBIGUOUS_DESCRIPTION,
            ),
        )
        expected = tuple(
            sorted(
                (
                    IssueType.MISSING_TECHNICAL_ATTRIBUTE,
                    IssueType.INVALID_UNIT,
                    IssueType.AMBIGUOUS_DESCRIPTION,
                ),
                key=lambda x: x.value,
            )
        )
        self.assertEqual(pred.predicted_issue_types, expected)

    def test_frozen_immutability(self) -> None:
        pred = MaterialRulePrediction(
            material_id="MAT-001",
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        with self.assertRaises(FrozenInstanceError):
            pred.material_id = "MAT-002"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            pred.predicted_issue_types = ()  # type: ignore[misc]

    def test_slots_no_dict(self) -> None:
        pred = MaterialRulePrediction(
            material_id="MAT-001",
            predicted_issue_types=(),
        )
        self.assertFalse(hasattr(pred, "__dict__"))


class MaterialRuleCaseEvaluationTests(unittest.TestCase):
    """Testes unitários defensivos para MaterialRuleCaseEvaluation."""

    def test_valid_creation_and_fields(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id, "MAT-001")
        self.assertEqual(evaluation.expected_issue_types, (IssueType.INVALID_UNIT,))
        self.assertEqual(evaluation.predicted_issue_types, (IssueType.INVALID_UNIT,))
        self.assertTrue(evaluation.is_match)
        self.assertFalse(evaluation.is_mismatch)

    def test_string_fields_normalized_with_strip(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="  CASE-001 \t",
            ground_truth_id=" GT-001\n",
            material_id=" MAT-001 ",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id, "MAT-001")

    def test_string_fields_reject_empty_or_whitespace(self) -> None:
        fields = ("evaluation_case_id", "ground_truth_id", "material_id")
        for field_name in fields:
            for invalid_val in ("", "   ", "\t\n"):
                kwargs = {
                    "evaluation_case_id": "CASE-001",
                    "ground_truth_id": "GT-001",
                    "material_id": "MAT-001",
                    "expected_issue_types": (),
                    "predicted_issue_types": (),
                }
                kwargs[field_name] = invalid_val
                with self.subTest(field=field_name, value=invalid_val):
                    with self.assertRaises(ValueError):
                        MaterialRuleCaseEvaluation(**kwargs)

    def test_string_fields_reject_invalid_types(self) -> None:
        fields = ("evaluation_case_id", "ground_truth_id", "material_id")
        for field_name in fields:
            for invalid_type in (None, 123, True, False, []):
                kwargs = {
                    "evaluation_case_id": "CASE-001",
                    "ground_truth_id": "GT-001",
                    "material_id": "MAT-001",
                    "expected_issue_types": (),
                    "predicted_issue_types": (),
                }
                kwargs[field_name] = invalid_type
                with self.subTest(field=field_name, type=type(invalid_type).__name__):
                    with self.assertRaises(TypeError):
                        MaterialRuleCaseEvaluation(**kwargs)

    def test_issue_types_tuples_validation(self) -> None:
        for field_name in ("expected_issue_types", "predicted_issue_types"):
            kwargs_base = {
                "evaluation_case_id": "CASE-001",
                "ground_truth_id": "GT-001",
                "material_id": "MAT-001",
                "expected_issue_types": (),
                "predicted_issue_types": (),
            }

            kwargs = dict(kwargs_base, **{field_name: [IssueType.INVALID_UNIT]})
            with self.subTest(field=field_name, case="non_tuple"):
                with self.assertRaises(TypeError):
                    MaterialRuleCaseEvaluation(**kwargs)

            kwargs = dict(kwargs_base, **{field_name: ("INVALID_UNIT",)})
            with self.subTest(field=field_name, case="non_enum"):
                with self.assertRaises(TypeError):
                    MaterialRuleCaseEvaluation(**kwargs)

            kwargs = dict(kwargs_base, **{field_name: (IssueType.POSSIBLE_DUPLICATE,)})
            with self.subTest(field=field_name, case="possible_duplicate"):
                with self.assertRaises(ValueError):
                    MaterialRuleCaseEvaluation(**kwargs)

            kwargs = dict(
                kwargs_base,
                **{field_name: (IssueType.INVALID_UNIT, IssueType.INVALID_UNIT)},
            )
            with self.subTest(field=field_name, case="duplicates"):
                with self.assertRaises(ValueError):
                    MaterialRuleCaseEvaluation(**kwargs)

    def test_exact_match_clean_both_empty(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        self.assertTrue(evaluation.is_match)
        self.assertFalse(evaluation.is_mismatch)
        self.assertTrue(evaluation.is_clean_match)
        self.assertFalse(evaluation.is_defect_match)
        self.assertEqual(evaluation.false_positives, ())
        self.assertEqual(evaluation.false_negatives, ())
        self.assertEqual(evaluation.true_positives, ())
        self.assertFalse(evaluation.has_false_positives)
        self.assertFalse(evaluation.has_false_negatives)

    def test_exact_match_with_defects(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD),
            predicted_issue_types=(IssueType.MISSING_CRITICAL_FIELD, IssueType.INVALID_UNIT),
        )
        self.assertTrue(evaluation.is_match)
        self.assertFalse(evaluation.is_mismatch)
        self.assertFalse(evaluation.is_clean_match)
        self.assertTrue(evaluation.is_defect_match)
        self.assertEqual(evaluation.false_positives, ())
        self.assertEqual(evaluation.false_negatives, ())
        self.assertEqual(
            evaluation.true_positives,
            tuple(sorted((IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD), key=lambda x: x.value)),
        )
        self.assertFalse(evaluation.has_false_positives)
        self.assertFalse(evaluation.has_false_negatives)

    def test_mismatch_false_positives_only(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        self.assertFalse(evaluation.is_match)
        self.assertTrue(evaluation.is_mismatch)
        self.assertFalse(evaluation.is_clean_match)
        self.assertFalse(evaluation.is_defect_match)
        self.assertEqual(evaluation.false_positives, (IssueType.INVALID_UNIT,))
        self.assertEqual(evaluation.false_negatives, ())
        self.assertEqual(evaluation.true_positives, ())
        self.assertTrue(evaluation.has_false_positives)
        self.assertFalse(evaluation.has_false_negatives)

    def test_mismatch_false_negatives_only(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(),
        )
        self.assertFalse(evaluation.is_match)
        self.assertTrue(evaluation.is_mismatch)
        self.assertFalse(evaluation.is_clean_match)
        self.assertFalse(evaluation.is_defect_match)
        self.assertEqual(evaluation.false_positives, ())
        self.assertEqual(evaluation.false_negatives, (IssueType.INVALID_UNIT,))
        self.assertEqual(evaluation.true_positives, ())
        self.assertFalse(evaluation.has_false_positives)
        self.assertTrue(evaluation.has_false_negatives)

    def test_partial_overlap(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD),
            predicted_issue_types=(IssueType.INVALID_UNIT, IssueType.AMBIGUOUS_DESCRIPTION),
        )
        self.assertFalse(evaluation.is_match)
        self.assertTrue(evaluation.is_mismatch)
        self.assertEqual(evaluation.true_positives, (IssueType.INVALID_UNIT,))
        self.assertEqual(evaluation.false_positives, (IssueType.AMBIGUOUS_DESCRIPTION,))
        self.assertEqual(evaluation.false_negatives, (IssueType.MISSING_CRITICAL_FIELD,))
        self.assertTrue(evaluation.has_false_positives)
        self.assertTrue(evaluation.has_false_negatives)

    def test_total_disjunction(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(IssueType.AMBIGUOUS_DESCRIPTION,),
        )
        self.assertFalse(evaluation.is_match)
        self.assertTrue(evaluation.is_mismatch)
        self.assertEqual(evaluation.true_positives, ())
        self.assertEqual(evaluation.false_positives, (IssueType.AMBIGUOUS_DESCRIPTION,))
        self.assertEqual(evaluation.false_negatives, (IssueType.INVALID_UNIT,))
        self.assertTrue(evaluation.has_false_positives)
        self.assertTrue(evaluation.has_false_negatives)

    def test_canonical_sorting_of_sets(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(
                IssueType.MISSING_TECHNICAL_ATTRIBUTE,
                IssueType.INVALID_UNIT,
            ),
            predicted_issue_types=(
                IssueType.AMBIGUOUS_DESCRIPTION,
                IssueType.INVALID_STATUS,
            ),
        )
        self.assertIsInstance(evaluation.false_positives, tuple)
        self.assertIsInstance(evaluation.false_negatives, tuple)
        self.assertIsInstance(evaluation.true_positives, tuple)
        self.assertEqual(
            evaluation.false_positives,
            tuple(sorted(evaluation.false_positives, key=lambda x: x.value)),
        )
        self.assertEqual(
            evaluation.false_negatives,
            tuple(sorted(evaluation.false_negatives, key=lambda x: x.value)),
        )

    def test_frozen_immutability(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        with self.assertRaises(FrozenInstanceError):
            evaluation.material_id = "MAT-002"  # type: ignore[misc]

    def test_slots_no_dict(self) -> None:
        evaluation = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        self.assertFalse(hasattr(evaluation, "__dict__"))


class EvaluateMaterialRuleTests(unittest.TestCase):
    """Testes para a função atômica evaluate_material_rule."""

    def test_successful_atomic_evaluation(self) -> None:
        gt = _make_rule_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
        )
        pred = _make_rule_prediction(
            material_id="MAT-001",
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        res = evaluate_material_rule(gt, pred)
        self.assertIsInstance(res, MaterialRuleCaseEvaluation)
        self.assertEqual(res.evaluation_case_id, "CASE-001")
        self.assertEqual(res.ground_truth_id, "GT-001")
        self.assertEqual(res.material_id, "MAT-001")
        self.assertEqual(res.expected_issue_types, (IssueType.INVALID_UNIT,))
        self.assertEqual(res.predicted_issue_types, (IssueType.INVALID_UNIT,))
        self.assertTrue(res.is_match)

    def test_rejects_non_ground_truth_instance(self) -> None:
        pred = _make_rule_prediction()
        with self.assertRaises(TypeError):
            evaluate_material_rule("invalid", pred)  # type: ignore[arg-type]

    def test_rejects_non_prediction_instance(self) -> None:
        gt = _make_rule_ground_truth()
        with self.assertRaises(TypeError):
            evaluate_material_rule(gt, "invalid")  # type: ignore[arg-type]

    def test_rejects_material_id_mismatch(self) -> None:
        gt = _make_rule_ground_truth(material_id="MAT-001")
        pred = _make_rule_prediction(material_id="MAT-002")
        with self.assertRaises(ValueError) as ctx:
            evaluate_material_rule(gt, pred)
        self.assertIn("material_id mismatch", str(ctx.exception))


class MaterialRuleEvaluationReportTests(unittest.TestCase):
    """Testes para MaterialRuleEvaluationReport."""

    def test_valid_creation_and_canonical_ordering(self) -> None:
        c1 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        c2 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        report = MaterialRuleEvaluationReport(
            dataset_id="DS-001",
            cases=(c1, c2),
        )
        self.assertEqual(report.dataset_id, "DS-001")
        self.assertEqual(report.cases, (c2, c1))
        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 2)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertEqual(report.accuracy, 1.0)
        self.assertEqual(report.exact_match_ratio, 1.0)
        self.assertTrue(report.is_perfect_match)
        self.assertFalse(report.is_empty)

    def test_dataset_id_normalized_with_strip(self) -> None:
        report = MaterialRuleEvaluationReport(
            dataset_id="  DS-001 \t ",
            cases=(),
        )
        self.assertEqual(report.dataset_id, "DS-001")

    def test_dataset_id_rejects_empty_or_whitespace(self) -> None:
        for val in ("", "   ", "\t\n"):
            with self.subTest(value=val):
                with self.assertRaises(ValueError):
                    MaterialRuleEvaluationReport(dataset_id=val, cases=())

    def test_dataset_id_rejects_invalid_types(self) -> None:
        for val in (None, 123, True, False, []):
            with self.subTest(value=val):
                with self.assertRaises(TypeError):
                    MaterialRuleEvaluationReport(dataset_id=val, cases=())  # type: ignore[arg-type]

    def test_cases_must_be_tuple(self) -> None:
        with self.assertRaises(TypeError):
            MaterialRuleEvaluationReport(dataset_id="DS-001", cases=[])  # type: ignore[arg-type]

    def test_cases_rejects_invalid_elements(self) -> None:
        with self.assertRaises(TypeError):
            MaterialRuleEvaluationReport(dataset_id="DS-001", cases=("invalid",))  # type: ignore[arg-type]

    def test_cases_rejects_duplicate_evaluation_case_id(self) -> None:
        c1 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        c2 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        with self.assertRaises(ValueError) as ctx:
            MaterialRuleEvaluationReport(dataset_id="DS-001", cases=(c1, c2))
        self.assertIn("duplicate evaluation_case_id", str(ctx.exception))

    def test_metrics_computation(self) -> None:
        c1 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(IssueType.INVALID_UNIT,),
        )
        c2 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(IssueType.AMBIGUOUS_DESCRIPTION,),
        )
        c3 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-003",
            material_id="MAT-003",
            expected_issue_types=(IssueType.MISSING_CRITICAL_FIELD,),
            predicted_issue_types=(IssueType.MISSING_CRITICAL_FIELD, IssueType.INVALID_STATUS),
        )
        report = MaterialRuleEvaluationReport(dataset_id="DS-001", cases=(c1, c2, c3))
        self.assertEqual(report.total_cases, 3)
        self.assertEqual(report.matched_cases, 1)
        self.assertEqual(report.mismatched_cases, 2)
        self.assertEqual(report.accuracy, 1 / 3)
        self.assertEqual(report.exact_match_ratio, 1 / 3)
        self.assertEqual(report.total_false_positives, 2)
        self.assertEqual(report.total_false_negatives, 1)
        self.assertEqual(report.total_true_positives, 2)
        self.assertFalse(report.is_empty)
        self.assertFalse(report.is_perfect_match)
        self.assertEqual(report.matches, (c1,))
        self.assertEqual(report.mismatches, (c2, c3))

    def test_accuracy_is_exact_float_no_rounding(self) -> None:
        c1 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(),
            predicted_issue_types=(),
        )
        c2 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(),
        )
        c3 = MaterialRuleCaseEvaluation(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-003",
            material_id="MAT-003",
            expected_issue_types=(IssueType.INVALID_UNIT,),
            predicted_issue_types=(),
        )
        report = MaterialRuleEvaluationReport(dataset_id="DS-001", cases=(c1, c2, c3))
        self.assertEqual(report.accuracy, 1 / 3)
        self.assertEqual(report.exact_match_ratio, 1 / 3)
        self.assertNotEqual(report.accuracy, 0.33)

    def test_empty_report_semantics(self) -> None:
        report = MaterialRuleEvaluationReport(dataset_id="DS-001", cases=())
        self.assertEqual(report.total_cases, 0)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertIsNone(report.accuracy)
        self.assertIsNone(report.exact_match_ratio)
        self.assertEqual(report.total_false_positives, 0)
        self.assertEqual(report.total_false_negatives, 0)
        self.assertEqual(report.total_true_positives, 0)
        self.assertTrue(report.is_empty)
        self.assertFalse(report.is_perfect_match)
        self.assertEqual(report.matches, ())
        self.assertEqual(report.mismatches, ())

    def test_frozen_immutability(self) -> None:
        report = MaterialRuleEvaluationReport(dataset_id="DS-001", cases=())
        with self.assertRaises(FrozenInstanceError):
            report.dataset_id = "DS-002"  # type: ignore[misc]

    def test_slots_no_dict(self) -> None:
        report = MaterialRuleEvaluationReport(dataset_id="DS-001", cases=())
        self.assertFalse(hasattr(report, "__dict__"))


class EvaluateMaterialRulesBatchTests(unittest.TestCase):
    """Testes para evaluate_material_rules em lote."""

    def test_successful_batch_evaluation(self) -> None:
        gt1 = _make_rule_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_issue_types=(IssueType.INVALID_UNIT,),
        )
        gt2 = _make_rule_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
            expected_issue_types=(),
        )
        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt1, gt2),
        )
        preds = {
            "CASE-001": _make_rule_prediction(
                material_id="MAT-001",
                predicted_issue_types=(IssueType.INVALID_UNIT,),
            ),
            "CASE-002": _make_rule_prediction(
                material_id="MAT-002",
                predicted_issue_types=(),
            ),
        }
        report = evaluate_material_rules(dataset, preds)
        self.assertEqual(report.dataset_id, "DS-001")
        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 2)
        self.assertTrue(report.is_perfect_match)

    def test_dataset_type_invalid(self) -> None:
        with self.assertRaises(TypeError):
            evaluate_material_rules("invalid", {})  # type: ignore[arg-type]

    def test_predictions_not_mapping(self) -> None:
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=())
        with self.assertRaises(TypeError):
            evaluate_material_rules(dataset, [])  # type: ignore[arg-type]

    def test_predictions_key_invalid_type(self) -> None:
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=())
        invalid_keys = (123, True, False, None)
        for k in invalid_keys:
            with self.subTest(key=k):
                with self.assertRaises(TypeError):
                    evaluate_material_rules(dataset, {k: _make_rule_prediction()})  # type: ignore[dict-item]

    def test_predictions_value_invalid_type(self) -> None:
        gt = _make_rule_ground_truth(evaluation_case_id="CASE-001")
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=(gt,))
        with self.assertRaises(TypeError):
            evaluate_material_rules(dataset, {"CASE-001": "invalid"})  # type: ignore[dict-item]

    def test_missing_evaluation_case_id(self) -> None:
        gt1 = _make_rule_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        gt2 = _make_rule_ground_truth(evaluation_case_id="CASE-002", ground_truth_id="GT-002")
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=(gt1, gt2))
        preds = {
            "CASE-001": _make_rule_prediction(),
        }
        with self.assertRaises(ValueError) as ctx:
            evaluate_material_rules(dataset, preds)
        self.assertIn("missing predictions for evaluation_case_id", str(ctx.exception))

    def test_extra_evaluation_case_id(self) -> None:
        gt1 = _make_rule_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=(gt1,))
        preds = {
            "CASE-001": _make_rule_prediction(),
            "CASE-002": _make_rule_prediction(),
        }
        with self.assertRaises(ValueError) as ctx:
            evaluate_material_rules(dataset, preds)
        self.assertIn("unexpected predictions for evaluation_case_id", str(ctx.exception))

    def test_material_id_mismatch_in_batch(self) -> None:
        gt1 = _make_rule_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001", material_id="MAT-001")
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=(gt1,))
        preds = {
            "CASE-001": _make_rule_prediction(material_id="MAT-002"),
        }
        with self.assertRaises(ValueError) as ctx:
            evaluate_material_rules(dataset, preds)
        self.assertIn("material_id mismatch for evaluation_case_id", str(ctx.exception))

    def test_mapping_order_independence(self) -> None:
        gt1 = _make_rule_ground_truth(evaluation_case_id="CASE-001", ground_truth_id="GT-001")
        gt2 = _make_rule_ground_truth(evaluation_case_id="CASE-002", ground_truth_id="GT-002")
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=(gt1, gt2))
        preds = {
            "CASE-002": _make_rule_prediction(),
            "CASE-001": _make_rule_prediction(),
        }
        report = evaluate_material_rules(dataset, preds)
        self.assertEqual(report.cases[0].evaluation_case_id, "CASE-001")
        self.assertEqual(report.cases[1].evaluation_case_id, "CASE-002")

    def test_empty_dataset_and_predictions(self) -> None:
        dataset = MaterialRuleGroundTruthDataset(dataset_id="DS-001", items=())
        report = evaluate_material_rules(dataset, {})
        self.assertEqual(report.dataset_id, "DS-001")
        self.assertEqual(report.total_cases, 0)
        self.assertTrue(report.is_empty)
        self.assertIsNone(report.accuracy)
        self.assertIsNone(report.exact_match_ratio)

    def test_preserves_dataset_id(self) -> None:
        dataset = MaterialRuleGroundTruthDataset(dataset_id="CUSTOM-DATASET-42", items=())
        report = evaluate_material_rules(dataset, {})
        self.assertEqual(report.dataset_id, "CUSTOM-DATASET-42")


class GroundTruthEvaluationPublicExportsTests(unittest.TestCase):
    """Testes de disponibilidade dos símbolos canônicos na API pública raiz (agent_lab)."""

    def test_symbols_exported_at_root_package(self) -> None:
        import agent_lab

        expected_symbols = (
            "DecisionRecommendationCaseEvaluation",
            "DecisionRecommendationEvaluationReport",
            "evaluate_decision_recommendation",
            "evaluate_decision_recommendations",
            "MaterialRulePrediction",
            "MaterialRuleCaseEvaluation",
            "MaterialRuleEvaluationReport",
            "evaluate_material_rule",
            "evaluate_material_rules",
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
            "MaterialRulePrediction",
            "MaterialRuleCaseEvaluation",
            "MaterialRuleEvaluationReport",
            "evaluate_material_rule",
            "evaluate_material_rules",
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
            MaterialRuleCaseEvaluation as DirectRuleCaseEval,
            MaterialRuleEvaluationReport as DirectRuleReport,
            MaterialRulePrediction as DirectRulePred,
            evaluate_decision_recommendation as direct_eval_one,
            evaluate_decision_recommendations as direct_eval_batch,
            evaluate_material_rule as direct_eval_rule_one,
            evaluate_material_rules as direct_eval_rule_batch,
        )

        self.assertIs(DirectCaseEval, DecisionRecommendationCaseEvaluation)
        self.assertIs(DirectReport, DecisionRecommendationEvaluationReport)
        self.assertIs(direct_eval_one, evaluate_decision_recommendation)
        self.assertIs(direct_eval_batch, evaluate_decision_recommendations)
        self.assertIs(DirectRulePred, MaterialRulePrediction)
        self.assertIs(DirectRuleCaseEval, MaterialRuleCaseEvaluation)
        self.assertIs(DirectRuleReport, MaterialRuleEvaluationReport)
        self.assertIs(direct_eval_rule_one, evaluate_material_rule)
        self.assertIs(direct_eval_rule_batch, evaluate_material_rules)


class DuplicatePairPredictionTests(unittest.TestCase):
    """Testes unitários e defensivos para DuplicatePairPrediction (Slice 1)."""

    def test_nominal_construction_and_fields(self) -> None:
        pred_true = DuplicatePairPrediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        self.assertEqual(pred_true.material_id_a, "MAT-001")
        self.assertEqual(pred_true.material_id_b, "MAT-002")
        self.assertIs(pred_true.is_duplicate, True)

        pred_false = DuplicatePairPrediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=False,
        )
        self.assertEqual(pred_false.material_id_a, "MAT-001")
        self.assertEqual(pred_false.material_id_b, "MAT-002")
        self.assertIs(pred_false.is_duplicate, False)

    def test_string_fields_normalized_with_strip(self) -> None:
        pred = DuplicatePairPrediction(
            material_id_a="  MAT-001  ",
            material_id_b="\tMAT-002 \n",
            is_duplicate=True,
        )
        self.assertEqual(pred.material_id_a, "MAT-001")
        self.assertEqual(pred.material_id_b, "MAT-002")

    def test_ordering_evaluated_after_normalization(self) -> None:
        pred = DuplicatePairPrediction(
            material_id_a="   MAT-001   ",
            material_id_b=" MAT-002 ",
            is_duplicate=False,
        )
        self.assertEqual(pred.material_id_a, "MAT-001")
        self.assertEqual(pred.material_id_b, "MAT-002")

    def test_immutability_frozen_instance(self) -> None:
        pred = DuplicatePairPrediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        with self.assertRaises(FrozenInstanceError):
            pred.material_id_a = "MAT-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            pred.material_id_b = "MAT-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            pred.is_duplicate = False  # type: ignore[misc]

    def test_rejects_non_string_material_ids(self) -> None:
        invalid_types = (123, 45.6, True, False, None, object(), [], {})
        for val in invalid_types:
            with self.subTest(field="material_id_a", value=val):
                with self.assertRaises(TypeError) as ctx:
                    DuplicatePairPrediction(
                        material_id_a=val,  # type: ignore[arg-type]
                        material_id_b="MAT-002",
                        is_duplicate=True,
                    )
                self.assertIn("material_id_a must be a str", str(ctx.exception))
            with self.subTest(field="material_id_b", value=val):
                with self.assertRaises(TypeError) as ctx:
                    DuplicatePairPrediction(
                        material_id_a="MAT-001",
                        material_id_b=val,  # type: ignore[arg-type]
                        is_duplicate=True,
                    )
                self.assertIn("material_id_b must be a str", str(ctx.exception))

    def test_rejects_empty_or_whitespace_material_ids(self) -> None:
        invalid_strings = ("", "   ", "\t\n", "\r\n  \t")
        for val in invalid_strings:
            with self.subTest(field="material_id_a", value=repr(val)):
                with self.assertRaises(ValueError) as ctx:
                    DuplicatePairPrediction(
                        material_id_a=val,
                        material_id_b="MAT-002",
                        is_duplicate=True,
                    )
                self.assertIn(
                    "material_id_a must not be empty or whitespace",
                    str(ctx.exception),
                )
            with self.subTest(field="material_id_b", value=repr(val)):
                with self.assertRaises(ValueError) as ctx:
                    DuplicatePairPrediction(
                        material_id_a="MAT-001",
                        material_id_b=val,
                        is_duplicate=True,
                    )
                self.assertIn(
                    "material_id_b must not be empty or whitespace",
                    str(ctx.exception),
                )

    def test_rejects_self_pair_equal_ids(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            DuplicatePairPrediction(
                material_id_a="MAT-001",
                material_id_b="MAT-001",
                is_duplicate=True,
            )
        self.assertEqual(
            str(ctx.exception),
            "material_id_a and material_id_b must be different",
        )

    def test_rejects_self_pair_equal_ids_after_strip(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            DuplicatePairPrediction(
                material_id_a=" MAT-001 ",
                material_id_b="MAT-001",
                is_duplicate=False,
            )
        self.assertEqual(
            str(ctx.exception),
            "material_id_a and material_id_b must be different",
        )

    def test_rejects_inverted_pair_order(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            DuplicatePairPrediction(
                material_id_a="MAT-002",
                material_id_b="MAT-001",
                is_duplicate=True,
            )
        self.assertEqual(
            str(ctx.exception),
            "material_id_a must be less than material_id_b",
        )

    def test_rejects_inverted_pair_order_after_strip(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            DuplicatePairPrediction(
                material_id_a=" MAT-002 ",
                material_id_b=" MAT-001 ",
                is_duplicate=False,
            )
        self.assertEqual(
            str(ctx.exception),
            "material_id_a must be less than material_id_b",
        )

    def test_rejects_non_bool_is_duplicate(self) -> None:
        invalid_values = (0, 1, "True", "False", None, 0.0, 1.0, [], {})
        for val in invalid_values:
            with self.subTest(value=val):
                with self.assertRaises(TypeError) as ctx:
                    DuplicatePairPrediction(
                        material_id_a="MAT-001",
                        material_id_b="MAT-002",
                        is_duplicate=val,  # type: ignore[arg-type]
                    )
                self.assertEqual(str(ctx.exception), "is_duplicate must be a bool")


class DuplicatePairCaseEvaluationTests(unittest.TestCase):
    """Testes unitários e defensivos para DuplicatePairCaseEvaluation (Slice 2)."""

    def test_nominal_construction_and_fields(self) -> None:
        evaluation = DuplicatePairCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            expected_is_duplicate=True,
            predicted_is_duplicate=True,
        )

        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id_a, "MAT-001")
        self.assertEqual(evaluation.material_id_b, "MAT-002")
        self.assertIs(evaluation.expected_is_duplicate, True)
        self.assertIs(evaluation.predicted_is_duplicate, True)
        self.assertTrue(evaluation.is_match)
        self.assertFalse(evaluation.is_mismatch)

    def test_string_fields_normalized_with_strip(self) -> None:
        evaluation = DuplicatePairCaseEvaluation(
            evaluation_case_id="  CASE-001  ",
            ground_truth_id="  GT-001\t",
            material_id_a=" \nMAT-001 ",
            material_id_b=" MAT-002\r\n",
            expected_is_duplicate=False,
            predicted_is_duplicate=False,
        )

        self.assertEqual(evaluation.evaluation_case_id, "CASE-001")
        self.assertEqual(evaluation.ground_truth_id, "GT-001")
        self.assertEqual(evaluation.material_id_a, "MAT-001")
        self.assertEqual(evaluation.material_id_b, "MAT-002")

    def test_immutability_frozen_instance(self) -> None:
        evaluation = DuplicatePairCaseEvaluation(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            expected_is_duplicate=True,
            predicted_is_duplicate=True,
        )

        with self.assertRaises(FrozenInstanceError):
            evaluation.evaluation_case_id = "CASE-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            evaluation.ground_truth_id = "GT-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            evaluation.material_id_a = "MAT-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            evaluation.material_id_b = "MAT-099"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            evaluation.expected_is_duplicate = False  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            evaluation.predicted_is_duplicate = False  # type: ignore[misc]

    def test_truth_table_complete(self) -> None:
        cases = (
            (False, False, True, False),
            (False, True, False, True),
            (True, False, False, True),
            (True, True, True, False),
        )

        for expected, predicted, exp_match, exp_mismatch in cases:
            with self.subTest(expected=expected, predicted=predicted):
                evaluation = DuplicatePairCaseEvaluation(
                    evaluation_case_id="CASE-001",
                    ground_truth_id="GT-001",
                    material_id_a="MAT-001",
                    material_id_b="MAT-002",
                    expected_is_duplicate=expected,
                    predicted_is_duplicate=predicted,
                )
                self.assertIs(evaluation.is_match, exp_match)
                self.assertIs(evaluation.is_mismatch, exp_mismatch)

    def test_rejects_non_string_text_fields(self) -> None:
        invalid_types = (123, 45.6, True, False, None, object(), [], {})
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id_a",
            "material_id_b",
        )

        for field_name in text_fields:
            for val in invalid_types:
                kwargs: dict[str, object] = {
                    "evaluation_case_id": "CASE-001",
                    "ground_truth_id": "GT-001",
                    "material_id_a": "MAT-001",
                    "material_id_b": "MAT-002",
                    "expected_is_duplicate": True,
                    "predicted_is_duplicate": True,
                }
                kwargs[field_name] = val
                with self.subTest(field=field_name, value=val):
                    with self.assertRaises(TypeError) as ctx:
                        DuplicatePairCaseEvaluation(**kwargs)  # type: ignore[arg-type]
                    self.assertIn(f"{field_name} must be a str", str(ctx.exception))

    def test_rejects_empty_or_whitespace_text_fields(self) -> None:
        invalid_strings = ("", "   ", "\t\n", "\r\n \t")
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id_a",
            "material_id_b",
        )

        for field_name in text_fields:
            for val in invalid_strings:
                kwargs: dict[str, object] = {
                    "evaluation_case_id": "CASE-001",
                    "ground_truth_id": "GT-001",
                    "material_id_a": "MAT-001",
                    "material_id_b": "MAT-002",
                    "expected_is_duplicate": True,
                    "predicted_is_duplicate": True,
                }
                kwargs[field_name] = val
                with self.subTest(field=field_name, value=repr(val)):
                    with self.assertRaises(ValueError) as ctx:
                        DuplicatePairCaseEvaluation(**kwargs)
                    self.assertIn(
                        f"{field_name} must not be empty or whitespace",
                        str(ctx.exception),
                    )

    def test_rejects_non_bool_expected_is_duplicate(self) -> None:
        invalid_values = (0, 1, "True", "False", None, 0.0, 1.0, [], {})
        for val in invalid_values:
            with self.subTest(value=val):
                with self.assertRaises(TypeError) as ctx:
                    DuplicatePairCaseEvaluation(
                        evaluation_case_id="CASE-001",
                        ground_truth_id="GT-001",
                        material_id_a="MAT-001",
                        material_id_b="MAT-002",
                        expected_is_duplicate=val,  # type: ignore[arg-type]
                        predicted_is_duplicate=True,
                    )
                self.assertEqual(
                    str(ctx.exception),
                    "expected_is_duplicate must be a bool",
                )

    def test_rejects_non_bool_predicted_is_duplicate(self) -> None:
        invalid_values = (0, 1, "True", "False", None, 0.0, 1.0, [], {})
        for val in invalid_values:
            with self.subTest(value=val):
                with self.assertRaises(TypeError) as ctx:
                    DuplicatePairCaseEvaluation(
                        evaluation_case_id="CASE-001",
                        ground_truth_id="GT-001",
                        material_id_a="MAT-001",
                        material_id_b="MAT-002",
                        expected_is_duplicate=True,
                        predicted_is_duplicate=val,  # type: ignore[arg-type]
                    )
                self.assertEqual(
                    str(ctx.exception),
                    "predicted_is_duplicate must be a bool",
                )


class EvaluateDuplicatePairTests(unittest.TestCase):
    """Testes para a função atômica evaluate_duplicate_pair (Slice 3)."""

    def test_evaluates_matching_duplicate_pair(self) -> None:
        # Match True / True
        gt_true = _make_duplicate_pair_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        pred_true = _make_duplicate_pair_prediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        res_true = evaluate_duplicate_pair(gt_true, pred_true)
        self.assertIsInstance(res_true, DuplicatePairCaseEvaluation)
        self.assertEqual(res_true.evaluation_case_id, "CASE-001")
        self.assertEqual(res_true.ground_truth_id, "GT-001")
        self.assertEqual(res_true.material_id_a, "MAT-001")
        self.assertEqual(res_true.material_id_b, "MAT-002")
        self.assertIs(res_true.expected_is_duplicate, True)
        self.assertIs(res_true.predicted_is_duplicate, True)
        self.assertTrue(res_true.is_match)
        self.assertFalse(res_true.is_mismatch)

        # Match False / False
        gt_false = _make_duplicate_pair_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=False,
        )
        pred_false = _make_duplicate_pair_prediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=False,
        )
        res_false = evaluate_duplicate_pair(gt_false, pred_false)
        self.assertIs(res_false.expected_is_duplicate, False)
        self.assertIs(res_false.predicted_is_duplicate, False)
        self.assertTrue(res_false.is_match)
        self.assertFalse(res_false.is_mismatch)

    def test_evaluates_mismatching_duplicate_pair(self) -> None:
        # Mismatch True / False (esperado True, predito False)
        gt_true = _make_duplicate_pair_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        pred_false = _make_duplicate_pair_prediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=False,
        )
        res_1 = evaluate_duplicate_pair(gt_true, pred_false)
        self.assertIs(res_1.expected_is_duplicate, True)
        self.assertIs(res_1.predicted_is_duplicate, False)
        self.assertFalse(res_1.is_match)
        self.assertTrue(res_1.is_mismatch)

        # Mismatch False / True (esperado False, predito True)
        gt_false = _make_duplicate_pair_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=False,
        )
        pred_true = _make_duplicate_pair_prediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
            is_duplicate=True,
        )
        res_2 = evaluate_duplicate_pair(gt_false, pred_true)
        self.assertIs(res_2.expected_is_duplicate, False)
        self.assertIs(res_2.predicted_is_duplicate, True)
        self.assertFalse(res_2.is_match)
        self.assertTrue(res_2.is_mismatch)

    def test_preserves_case_and_ground_truth_lineage(self) -> None:
        gt = _make_duplicate_pair_ground_truth(
            evaluation_case_id="CASE-XYZ-999",
            ground_truth_id="GT-ABC-123",
            material_id_a="MAT-010",
            material_id_b="MAT-020",
            is_duplicate=True,
        )
        pred = _make_duplicate_pair_prediction(
            material_id_a="MAT-010",
            material_id_b="MAT-020",
            is_duplicate=True,
        )
        res = evaluate_duplicate_pair(gt, pred)
        self.assertEqual(res.evaluation_case_id, "CASE-XYZ-999")
        self.assertEqual(res.ground_truth_id, "GT-ABC-123")
        self.assertEqual(res.material_id_a, "MAT-010")
        self.assertEqual(res.material_id_b, "MAT-020")
        self.assertIs(res.expected_is_duplicate, True)
        self.assertIs(res.predicted_is_duplicate, True)

    def test_rejects_invalid_ground_truth_type(self) -> None:
        pred = _make_duplicate_pair_prediction()
        invalid_types = ("invalid", 123, 45.6, True, None, object(), [], {})
        for val in invalid_types:
            with self.subTest(value=val):
                with self.assertRaises(TypeError) as ctx:
                    evaluate_duplicate_pair(val, pred)  # type: ignore[arg-type]
                self.assertIn("ground_truth must be a DuplicatePairGroundTruth", str(ctx.exception))

    def test_rejects_invalid_prediction_type(self) -> None:
        gt = _make_duplicate_pair_ground_truth()
        invalid_types = ("invalid", 123, 45.6, True, None, object(), [], {})
        for val in invalid_types:
            with self.subTest(value=val):
                with self.assertRaises(TypeError) as ctx:
                    evaluate_duplicate_pair(gt, val)  # type: ignore[arg-type]
                self.assertIn("prediction must be a DuplicatePairPrediction", str(ctx.exception))

    def test_rejects_material_id_a_mismatch(self) -> None:
        gt = _make_duplicate_pair_ground_truth(
            material_id_a="MAT-001",
            material_id_b="MAT-003",
        )
        pred = _make_duplicate_pair_prediction(
            material_id_a="MAT-002",
            material_id_b="MAT-003",
        )
        with self.assertRaises(ValueError) as ctx:
            evaluate_duplicate_pair(gt, pred)
        self.assertIn("material pair mismatch", str(ctx.exception))

    def test_rejects_material_id_b_mismatch(self) -> None:
        gt = _make_duplicate_pair_ground_truth(
            material_id_a="MAT-001",
            material_id_b="MAT-003",
        )
        pred = _make_duplicate_pair_prediction(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
        )
        with self.assertRaises(ValueError) as ctx:
            evaluate_duplicate_pair(gt, pred)
        self.assertIn("material pair mismatch", str(ctx.exception))

    def test_rejects_both_material_ids_mismatch(self) -> None:
        gt = _make_duplicate_pair_ground_truth(
            material_id_a="MAT-001",
            material_id_b="MAT-002",
        )
        pred = _make_duplicate_pair_prediction(
            material_id_a="MAT-003",
            material_id_b="MAT-004",
        )
        with self.assertRaises(ValueError) as ctx:
            evaluate_duplicate_pair(gt, pred)
        self.assertIn("material pair mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
