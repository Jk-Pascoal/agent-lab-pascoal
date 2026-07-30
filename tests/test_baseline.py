import unittest
from pathlib import Path

from agent_lab.baseline import evaluate_baseline
from agent_lab.data_io import load_labeled_materials


DATASET = Path(__file__).parents[1] / "data" / "synthetic" / "materials.csv"
CHALLENGE_DATASET = (
    Path(__file__).parents[1] / "data" / "synthetic" / "materials_challenge.csv"
)


class BaselineEvaluationTests(unittest.TestCase):
    def test_baseline_processes_the_complete_dataset(self) -> None:
        materials = load_labeled_materials(DATASET)

        assessments, report = evaluate_baseline(materials)

        self.assertEqual(len(assessments), 20)
        self.assertEqual(report.total, 20)

    def test_baseline_reaches_minimum_quality_gate(self) -> None:
        materials = load_labeled_materials(DATASET)

        _, report = evaluate_baseline(materials)

        self.assertGreaterEqual(report.exact_match_accuracy, 0.75)
        self.assertGreaterEqual(report.duplicate_precision, 0.75)
        self.assertGreaterEqual(report.duplicate_recall, 0.75)

    def test_challenge_set_exposes_baseline_limitations(self) -> None:
        materials = load_labeled_materials(CHALLENGE_DATASET)

        _, report = evaluate_baseline(materials)

        self.assertGreaterEqual(report.exact_match_accuracy, 0.40)
        self.assertLess(report.exact_match_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
