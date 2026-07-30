import unittest

from agent_lab.domain import GovernanceDecision, IssueType, MaterialRecord
from agent_lab.duplicates import is_possible_duplicate
from agent_lab.validator import DeterministicGovernanceValidator


class DuplicateTests(unittest.TestCase):
    def test_detects_same_manufacturer_part_number(self) -> None:
        existing = MaterialRecord(
            material_id="MAT-0001",
            description_short="ROLAMENTO SKF 6205 ZZ",
            unit="PC",
            manufacturer="SKF",
            manufacturer_part_number="6205-2Z",
            material_group="ROLAMENTOS",
            status="ACTIVE",
        )
        incoming = MaterialRecord(
            material_id="MAT-0002",
            description_short="ROLAM. 6205 2Z SKF",
            unit="UN",
            manufacturer="SKF",
            manufacturer_part_number="6205-2Z",
            material_group="ROLAMENTOS",
            status="ACTIVE",
        )

        self.assertTrue(is_possible_duplicate(incoming, existing))

    def test_different_categories_are_not_duplicates(self) -> None:
        screw = MaterialRecord(
            material_id="MAT-0001",
            description_short="PARAFUSO M10",
            material_group="FIXADORES",
        )
        nut = MaterialRecord(
            material_id="MAT-0002",
            description_short="PORCA M10",
            material_group="FIXADORES",
        )

        self.assertFalse(is_possible_duplicate(nut, screw))


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = DeterministicGovernanceValidator()

    def test_missing_description_is_rejected(self) -> None:
        record = MaterialRecord(
            material_id="MAT-0007",
            description_short="",
            unit="PC",
            status="UNDER_REVIEW",
        )

        assessment = self.validator.analyze(record)

        self.assertEqual(assessment.decision, GovernanceDecision.REJECT)
        self.assertIn(
            IssueType.MISSING_CRITICAL_FIELD,
            {issue.issue_type for issue in assessment.issues},
        )

    def test_liquid_in_piece_unit_requires_review(self) -> None:
        record = MaterialRecord(
            material_id="MAT-0008",
            description_short="OLEO LUBRIFICANTE ISO VG 68",
            unit="PC",
            status="ACTIVE",
        )

        assessment = self.validator.analyze(record)

        self.assertEqual(assessment.decision, GovernanceDecision.REVIEW)
        self.assertIn(
            IssueType.SUSPICIOUS_UNIT,
            {issue.issue_type for issue in assessment.issues},
        )

    def test_complete_valid_material_is_approved(self) -> None:
        record = MaterialRecord(
            material_id="MAT-0012",
            description_short="PORCA SEXTAVADA M10",
            long_description="PORCA SEXTAVADA ROSCA METRICA M10 CLASSE 8",
            unit="PC",
            material_group="FIXADORES",
            status="ACTIVE",
        )

        assessment = self.validator.analyze(record)

        self.assertEqual(assessment.decision, GovernanceDecision.APPROVE)
        self.assertEqual(assessment.issues, ())


if __name__ == "__main__":
    unittest.main()

