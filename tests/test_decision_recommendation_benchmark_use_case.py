from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, MaterialRecord
from agent_lab.ground_truth import (
    DecisionRecommendationGroundTruth,
    DecisionRecommendationGroundTruthDataset,
    LabelProvenance,
)
from agent_lab.ground_truth_evaluation import (
    DecisionRecommendationEvaluationReport,
)
from agent_lab.decision_recommendation_benchmark_use_case import (
    DecisionRecommendationBenchmarkCase,
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
        source_reference="synthetic://spec-0141/test",
        annotator=None,
        labeled_at=datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc),
        rationale="Referência de teste para benchmark.",
    )


def _make_recommendation(
    *,
    material_id: str = "MAT-001",
    decision: GovernanceDecision = GovernanceDecision.APPROVE,
) -> DecisionRecommendation:
    return DecisionRecommendation(
        material_id=material_id,
        decision=decision,
        evidence=(),
        rationale="Recomendação gerada para teste de benchmark.",
    )


class DecisionRecommendationBenchmarkCaseTests(unittest.TestCase):
    def test_valid_case_construction_preserves_attributes(self) -> None:
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )

        self.assertEqual(case.evaluation_case_id, "CASE-001")
        self.assertIs(case.material, material)

    def test_semantic_independence_permits_identical_textual_values(
        self,
    ) -> None:
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="MAT-001",
            material=material,
        )

        self.assertEqual(case.evaluation_case_id, "MAT-001")
        self.assertEqual(case.material.material_id, "MAT-001")

    def test_same_material_can_participate_in_different_experimental_cases(
        self,
    ) -> None:
        material = MaterialRecord(material_id="MAT-001")
        case_1 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )
        case_2 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-002",
            material=material,
        )

        self.assertEqual(case_1.evaluation_case_id, "CASE-001")
        self.assertEqual(case_2.evaluation_case_id, "CASE-002")
        self.assertIs(case_1.material, case_2.material)

    def test_rejects_non_string_evaluation_case_id(self) -> None:
        material = MaterialRecord(material_id="MAT-001")
        for invalid_id in [123, None, ["CASE-001"], {"id": "CASE-001"}]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(TypeError):
                    DecisionRecommendationBenchmarkCase(
                        evaluation_case_id=invalid_id,  # type: ignore[arg-type]
                        material=material,
                    )

    def test_rejects_bool_evaluation_case_id(self) -> None:
        material = MaterialRecord(material_id="MAT-001")
        for bool_val in [True, False]:
            with self.subTest(bool_val=bool_val):
                with self.assertRaises(TypeError):
                    DecisionRecommendationBenchmarkCase(
                        evaluation_case_id=bool_val,  # type: ignore[arg-type]
                        material=material,
                    )

    def test_rejects_empty_evaluation_case_id(self) -> None:
        material = MaterialRecord(material_id="MAT-001")
        with self.assertRaises(ValueError):
            DecisionRecommendationBenchmarkCase(
                evaluation_case_id="",
                material=material,
            )

    def test_rejects_evaluation_case_id_with_outer_whitespace_fail_closed(
        self,
    ) -> None:
        material = MaterialRecord(material_id="MAT-001")
        for invalid_id in [
            " CASE-001",
            "CASE-001 ",
            "   ",
            "\tCASE-001",
            "CASE-001\n",
        ]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(ValueError):
                    DecisionRecommendationBenchmarkCase(
                        evaluation_case_id=invalid_id,
                        material=material,
                    )

    def test_rejects_non_material_record(self) -> None:
        for invalid_mat in [
            "MAT-001",
            None,
            123,
            {"material_id": "MAT-001"},
            object(),
        ]:
            with self.subTest(invalid_mat=invalid_mat):
                with self.assertRaises(TypeError):
                    DecisionRecommendationBenchmarkCase(
                        evaluation_case_id="CASE-001",
                        material=invalid_mat,  # type: ignore[arg-type]
                    )

    def test_immutability_frozen_instance(self) -> None:
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )

        with self.assertRaises(FrozenInstanceError):
            case.evaluation_case_id = "CASE-002"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            case.material = MaterialRecord(material_id="MAT-002")  # type: ignore[misc]

        self.assertFalse(hasattr(case, "__dict__"))


class RunDecisionRecommendationBenchmarkUseCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from agent_lab.decision_recommendation_benchmark_use_case import (
            RunDecisionRecommendationBenchmarkUseCase,
        )

        self.use_case_cls = RunDecisionRecommendationBenchmarkUseCase

    def test_nominal_execution_with_single_case_returns_official_evaluation_report(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            return _make_recommendation(
                material_id=mat.material_id,
                decision=GovernanceDecision.APPROVE,
            )

        use_case = self.use_case_cls(pipeline=pipeline)
        report = use_case.execute(dataset, [case])

        self.assertIsInstance(report, DecisionRecommendationEvaluationReport)
        self.assertEqual(report.dataset_id, "DS-001")
        self.assertEqual(report.total_cases, 1)
        self.assertEqual(report.matched_cases, 1)
        self.assertEqual(report.mismatched_cases, 0)
        self.assertEqual(report.accuracy, 1.0)
        self.assertTrue(report.is_perfect_match)
        self.assertEqual(len(report.cases), 1)
        self.assertEqual(report.cases[0].evaluation_case_id, "CASE-001")
        self.assertTrue(report.cases[0].is_match)

    def test_pipeline_receives_exact_material_instance_without_alteration(
        self,
    ) -> None:
        received_materials: list[MaterialRecord] = []
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        material = MaterialRecord(
            material_id="MAT-001",
            description_short="PARAFUSO SEXTAVADO",
        )
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            received_materials.append(mat)
            return _make_recommendation(
                material_id=mat.material_id,
                decision=GovernanceDecision.APPROVE,
            )

        use_case = self.use_case_cls(pipeline=pipeline)
        use_case.execute(dataset, [case])

        self.assertEqual(len(received_materials), 1)
        self.assertIs(received_materials[0], material)

    def test_indexing_uses_evaluation_case_id_and_not_material_id(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-ALPHA",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-ALPHA",
            material=material,
        )

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            return _make_recommendation(
                material_id=mat.material_id,
                decision=GovernanceDecision.APPROVE,
            )

        use_case = self.use_case_cls(pipeline=pipeline)
        report = use_case.execute(dataset, [case])

        self.assertEqual(report.total_cases, 1)
        self.assertEqual(report.cases[0].evaluation_case_id, "CASE-ALPHA")
        self.assertEqual(report.cases[0].material_id, "MAT-001")
        self.assertEqual(report.accuracy, 1.0)

    def test_same_material_in_different_experimental_cases_is_preserved_without_collapse(
        self,
    ) -> None:
        gt_1 = _make_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        gt_2 = _make_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt_1, gt_2),
        )
        material = MaterialRecord(material_id="MAT-001")
        case_1 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )
        case_2 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-002",
            material=material,
        )

        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(
                material_id=mat.material_id,
                decision=GovernanceDecision.APPROVE,
            )

        use_case = self.use_case_cls(pipeline=pipeline)
        report = use_case.execute(dataset, [case_1, case_2])

        self.assertEqual(len(calls), 2)
        self.assertEqual(report.total_cases, 2)
        self.assertEqual(report.matched_cases, 2)
        self.assertEqual(report.cases[0].evaluation_case_id, "CASE-001")
        self.assertEqual(report.cases[1].evaluation_case_id, "CASE-002")
        self.assertEqual(report.cases[0].material_id, "MAT-001")
        self.assertEqual(report.cases[1].material_id, "MAT-001")

    def test_mismatch_is_measured_by_evaluator_without_raising_execution_exception(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
            expected_recommendation=GovernanceDecision.APPROVE,
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        material = MaterialRecord(material_id="MAT-001")
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=material,
        )

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            return _make_recommendation(
                material_id=mat.material_id,
                decision=GovernanceDecision.REJECT,
            )

        use_case = self.use_case_cls(pipeline=pipeline)
        report = use_case.execute(dataset, [case])

        self.assertEqual(report.total_cases, 1)
        self.assertEqual(report.matched_cases, 0)
        self.assertEqual(report.mismatched_cases, 1)
        self.assertEqual(report.accuracy, 0.0)
        self.assertFalse(report.is_perfect_match)
        self.assertTrue(report.cases[0].is_mismatch)
        self.assertEqual(
            report.cases[0].expected_decision,
            GovernanceDecision.APPROVE,
        )
        self.assertEqual(
            report.cases[0].predicted_decision,
            GovernanceDecision.REJECT,
        )

    def test_rejects_non_dataset_object_without_invoking_pipeline(self) -> None:
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(material_id=mat.material_id)

        use_case = self.use_case_cls(pipeline=pipeline)

        for invalid_dataset in (None, "DS-001", object(), 123):
            with self.subTest(invalid_dataset=invalid_dataset):
                with self.assertRaises(TypeError):
                    use_case.execute(invalid_dataset, [case])  # type: ignore[arg-type]
                self.assertEqual(len(calls), 0)

    def test_rejects_non_sequence_or_str_bytes_cases_without_invoking_pipeline(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(material_id=mat.material_id)

        use_case = self.use_case_cls(pipeline=pipeline)

        for invalid_cases in (None, object(), "CASE-001", b"CASE-001", 123):
            with self.subTest(invalid_cases=invalid_cases):
                with self.assertRaises(TypeError):
                    use_case.execute(dataset, invalid_cases)  # type: ignore[arg-type]
                self.assertEqual(len(calls), 0)

    def test_rejects_invalid_case_element_without_invoking_pipeline_at_all(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        valid_case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(material_id=mat.material_id)

        use_case = self.use_case_cls(pipeline=pipeline)

        with self.assertRaises(TypeError):
            use_case.execute(dataset, [valid_case, object()])  # type: ignore[list-item]

        self.assertEqual(len(calls), 0)

    def test_rejects_duplicate_evaluation_case_id_without_invoking_pipeline(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        case_1 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        case_2 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(material_id=mat.material_id)

        use_case = self.use_case_cls(pipeline=pipeline)

        with self.assertRaises(ValueError):
            use_case.execute(dataset, [case_1, case_2])

        self.assertEqual(len(calls), 0)

    def test_rejects_pipeline_returning_non_decision_recommendation(
        self,
    ) -> None:
        gt_1 = _make_ground_truth(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-001",
        )
        gt_2 = _make_ground_truth(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-002",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt_1, gt_2),
        )
        case_1 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        case_2 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-002",
            material=MaterialRecord(material_id="MAT-002"),
        )

        for invalid_return in (None, object(), "APPROVE", 123):
            with self.subTest(invalid_return=invalid_return):
                calls: list[str] = []

                def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
                    calls.append(mat.material_id)
                    return invalid_return  # type: ignore[return-value]

                use_case = self.use_case_cls(pipeline=pipeline)

                with self.assertRaises(TypeError):
                    use_case.execute(dataset, [case_1, case_2])

                self.assertEqual(len(calls), 1)

    def test_rejects_prediction_with_mismatched_material_id_relative_to_case(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-999",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        case = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            return _make_recommendation(
                material_id="MAT-999",
                decision=GovernanceDecision.APPROVE,
            )

        use_case = self.use_case_cls(pipeline=pipeline)

        with self.assertRaises(ValueError):
            use_case.execute(dataset, [case])

    def test_rejects_sequence_with_invalid_element_without_partial_execution(
        self,
    ) -> None:
        gt = _make_ground_truth(
            evaluation_case_id="CASE-001",
            material_id="MAT-001",
        )
        dataset = DecisionRecommendationGroundTruthDataset(
            dataset_id="DS-001",
            items=(gt,),
        )
        case_1 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-001",
            material=MaterialRecord(material_id="MAT-001"),
        )
        case_2 = DecisionRecommendationBenchmarkCase(
            evaluation_case_id="CASE-002",
            material=MaterialRecord(material_id="MAT-002"),
        )
        calls: list[str] = []

        def pipeline(mat: MaterialRecord) -> DecisionRecommendation:
            calls.append(mat.material_id)
            return _make_recommendation(material_id=mat.material_id)

        use_case = self.use_case_cls(pipeline=pipeline)

        with self.assertRaises(TypeError):
            use_case.execute(dataset, [case_1, object(), case_2])  # type: ignore[list-item]

        self.assertEqual(len(calls), 0)


if __name__ == "__main__":
    unittest.main()
