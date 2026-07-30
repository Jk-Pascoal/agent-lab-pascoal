import unittest

from agent_lab.domain import (
    GovernanceAssessment,
    GovernanceDecision,
    MaterialRecord,
)
from agent_lab.metrics import completeness_score


class CompletenessScoreTests(unittest.TestCase):
    def test_complete_record_scores_one(self) -> None:
        record = MaterialRecord(
            material_id="MAT-0001",
            description_short="ROLAMENTO 6205",
            unit="PC",
            status="ACTIVE",
        )

        self.assertEqual(completeness_score(record), 1.0)

    def test_one_missing_required_field_reduces_score(self) -> None:
        record = MaterialRecord(
            material_id="MAT-0002",
            description_short="",
            unit="PC",
            status="UNDER_REVIEW",
        )

        self.assertEqual(completeness_score(record), 0.75)

    def test_empty_required_field_collection_is_rejected(self) -> None:
        record = MaterialRecord(material_id="MAT-0003")

        with self.assertRaises(ValueError):
            completeness_score(record, required_fields=())


class GovernanceAssessmentTests(unittest.TestCase):
    def test_scores_must_stay_between_zero_and_one(self) -> None:
        with self.assertRaises(ValueError):
            GovernanceAssessment(
                material_id="MAT-0001",
                completeness=1.1,
                confidence=0.8,
                decision=GovernanceDecision.REVIEW,
            )

    def test_valid_assessment_is_created(self) -> None:
        assessment = GovernanceAssessment(
            material_id="MAT-0001",
            completeness=1.0,
            confidence=0.9,
            decision=GovernanceDecision.APPROVE,
        )

        self.assertEqual(assessment.decision, GovernanceDecision.APPROVE)


if __name__ == "__main__":
    unittest.main()

