import unittest
from dataclasses import FrozenInstanceError

from agent_lab.domain import MaterialRecord
from agent_lab.decision_recommendation_benchmark_use_case import (
    DecisionRecommendationBenchmarkCase,
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


if __name__ == "__main__":
    unittest.main()
