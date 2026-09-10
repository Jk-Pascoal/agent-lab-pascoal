from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.domain import IssueType
from agent_lab.ground_truth import (
    LabelProvenance,
    MaterialRuleGroundTruth,
)
from agent_lab.human_review import VerifiedSpecialistIdentity


class GroundTruthSlice1Tests(unittest.TestCase):
    def test_label_provenance_members(self) -> None:
        self.assertEqual(
            LabelProvenance.SPECIALIST_CURATED.value,
            "SPECIALIST_CURATED",
        )
        self.assertEqual(
            LabelProvenance.SYNTHETIC_SPECIFIED.value,
            "SYNTHETIC_SPECIFIED",
        )

    def test_material_rule_ground_truth_synthetic_specified_minimal_valid(
        self,
    ) -> None:
        labeled_at = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)
        gt = MaterialRuleGroundTruth(
            evaluation_case_id="CASE-MAT-001",
            ground_truth_id="GT-RULE-001",
            material_id="MAT-1001",
            expected_issue_types=(),
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="SPEC-0115-FIXTURE-01",
            annotator=None,
            labeled_at=labeled_at,
            rationale="Material sem inconformidades cadastrais.",
        )

        self.assertEqual(gt.evaluation_case_id, "CASE-MAT-001")
        self.assertEqual(gt.ground_truth_id, "GT-RULE-001")
        self.assertEqual(gt.material_id, "MAT-1001")
        self.assertEqual(gt.expected_issue_types, ())
        self.assertEqual(gt.provenance, LabelProvenance.SYNTHETIC_SPECIFIED)
        self.assertEqual(gt.source_reference, "SPEC-0115-FIXTURE-01")
        self.assertIsNone(gt.annotator)
        self.assertEqual(gt.labeled_at, labeled_at)
        self.assertEqual(gt.rationale, "Material sem inconformidades cadastrais.")


class GroundTruthSlice2ExpectedIssueTypesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.labeled_at = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)

    def test_expected_issue_types_rejects_non_tuple_container(self) -> None:
        with self.assertRaises(TypeError):
            MaterialRuleGroundTruth(
                evaluation_case_id="CASE-MAT-001",
                ground_truth_id="GT-RULE-001",
                material_id="MAT-1001",
                expected_issue_types=[IssueType.INVALID_UNIT],  # type: ignore[arg-type]
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="SPEC-0115-FIXTURE-01",
                annotator=None,
                labeled_at=self.labeled_at,
                rationale="Material com unidade inválida.",
            )

    def test_expected_issue_types_rejects_non_issue_type_element(self) -> None:
        with self.assertRaises(TypeError):
            MaterialRuleGroundTruth(
                evaluation_case_id="CASE-MAT-001",
                ground_truth_id="GT-RULE-001",
                material_id="MAT-1001",
                expected_issue_types=("INVALID_UNIT",),  # type: ignore[arg-type]
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="SPEC-0115-FIXTURE-01",
                annotator=None,
                labeled_at=self.labeled_at,
                rationale="Material com unidade inválida.",
            )

    def test_expected_issue_types_rejects_possible_duplicate(self) -> None:
        with self.assertRaises(ValueError):
            MaterialRuleGroundTruth(
                evaluation_case_id="CASE-MAT-001",
                ground_truth_id="GT-RULE-001",
                material_id="MAT-1001",
                expected_issue_types=(IssueType.POSSIBLE_DUPLICATE,),
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="SPEC-0115-FIXTURE-01",
                annotator=None,
                labeled_at=self.labeled_at,
                rationale="Material com duplicidade.",
            )

    def test_expected_issue_types_rejects_duplicates(self) -> None:
        with self.assertRaises(ValueError):
            MaterialRuleGroundTruth(
                evaluation_case_id="CASE-MAT-001",
                ground_truth_id="GT-RULE-001",
                material_id="MAT-1001",
                expected_issue_types=(
                    IssueType.INVALID_UNIT,
                    IssueType.INVALID_UNIT,
                ),
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="SPEC-0115-FIXTURE-01",
                annotator=None,
                labeled_at=self.labeled_at,
                rationale="Material com unidade duplicada.",
            )

    def test_expected_issue_types_canonicalizes_order_by_issue_type_value(
        self,
    ) -> None:
        input_types = (
            IssueType.MISSING_CRITICAL_FIELD,
            IssueType.INVALID_UNIT,
        )
        expected_canonical = tuple(
            sorted(input_types, key=lambda item: item.value)
        )
        gt = MaterialRuleGroundTruth(
            evaluation_case_id="CASE-MAT-001",
            ground_truth_id="GT-RULE-001",
            material_id="MAT-1001",
            expected_issue_types=input_types,
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="SPEC-0115-FIXTURE-01",
            annotator=None,
            labeled_at=self.labeled_at,
            rationale="Material com múltiplos defeitos fora de ordem.",
        )
        self.assertEqual(gt.expected_issue_types, expected_canonical)


TEXT_FIELDS = (
    "evaluation_case_id",
    "ground_truth_id",
    "material_id",
    "source_reference",
    "rationale",
)


def _make_valid_material_rule_gt(**overrides: object) -> MaterialRuleGroundTruth:
    kwargs: dict[str, object] = {
        "evaluation_case_id": "CASE-MAT-001",
        "ground_truth_id": "GT-RULE-001",
        "material_id": "MAT-1001",
        "expected_issue_types": (),
        "provenance": LabelProvenance.SYNTHETIC_SPECIFIED,
        "source_reference": "SPEC-0115-FIXTURE-01",
        "annotator": None,
        "labeled_at": datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc),
        "rationale": "Material conforme.",
    }
    kwargs.update(overrides)
    return MaterialRuleGroundTruth(**kwargs)  # type: ignore[arg-type]


class GroundTruthSlice3TextFieldsTests(unittest.TestCase):
    def test_text_fields_reject_non_str(self) -> None:
        for field in TEXT_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    _make_valid_material_rule_gt(**{field: 123})

    def test_text_fields_reject_empty_or_whitespace(self) -> None:
        for field in TEXT_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    _make_valid_material_rule_gt(**{field: "   "})

    def test_text_fields_stripped(self) -> None:
        gt = _make_valid_material_rule_gt(
            evaluation_case_id="  CASE-MAT-001  ",
            ground_truth_id="  GT-RULE-001  ",
            material_id="  MAT-1001  ",
            source_reference="  SPEC-0115-FIXTURE-01  ",
            rationale="  Material conforme.  ",
        )
        self.assertEqual(gt.evaluation_case_id, "CASE-MAT-001")
        self.assertEqual(gt.ground_truth_id, "GT-RULE-001")
        self.assertEqual(gt.material_id, "MAT-1001")
        self.assertEqual(gt.source_reference, "SPEC-0115-FIXTURE-01")
        self.assertEqual(gt.rationale, "Material conforme.")


def _make_verified_specialist() -> VerifiedSpecialistIdentity:
    return VerifiedSpecialistIdentity(
        specialist_id="SPEC-001",
        identity_provider="TEST-IDP",
        identity_subject="subject-001",
        verification_id="VER-001",
        verified_at=datetime(
            2026, 9, 10, 8, 0,
            tzinfo=timezone.utc,
        ),
    )


class GroundTruthSlice4ProvenanceAnnotatorTests(unittest.TestCase):
    def test_provenance_rejects_string_equivalent(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_material_rule_gt(provenance="SYNTHETIC_SPECIFIED")

    def test_specialist_curated_rejects_none_annotator(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_material_rule_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=None,
            )

    def test_specialist_curated_rejects_non_specialist_annotator(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_material_rule_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator="SPEC-001",
            )

    def test_synthetic_specified_rejects_present_annotator(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_material_rule_gt(
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                annotator=_make_verified_specialist(),
            )

    def test_specialist_curated_valid(self) -> None:
        specialist = _make_verified_specialist()
        gt = _make_valid_material_rule_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
        )
        self.assertEqual(gt.provenance, LabelProvenance.SPECIALIST_CURATED)
        self.assertEqual(gt.annotator, specialist)


def _make_verified_specialist_at(
    verified_at: datetime,
) -> VerifiedSpecialistIdentity:
    return VerifiedSpecialistIdentity(
        specialist_id="SPEC-001",
        identity_provider="TEST-IDP",
        identity_subject="subject-001",
        verification_id="VER-001",
        verified_at=verified_at,
    )


class GroundTruthSlice5TemporalTests(unittest.TestCase):
    def test_labeled_at_rejects_non_datetime(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_material_rule_gt(
                labeled_at="2026-09-10T09:00:00Z",
            )

    def test_labeled_at_rejects_naive_datetime(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_material_rule_gt(
                labeled_at=datetime(2026, 9, 10, 9, 0),
            )

    def test_specialist_verified_at_cannot_be_after_labeled_at(self) -> None:
        labeled_at = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)
        specialist = _make_verified_specialist_at(
            datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc),
        )
        with self.assertRaises(ValueError):
            _make_valid_material_rule_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=specialist,
                labeled_at=labeled_at,
            )

    def test_specialist_verified_at_equal_to_labeled_at_is_valid(self) -> None:
        timestamp = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)
        specialist = _make_verified_specialist_at(timestamp)
        gt = _make_valid_material_rule_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
            labeled_at=timestamp,
        )
        self.assertEqual(gt.labeled_at, timestamp)
        self.assertEqual(gt.annotator, specialist)


class GroundTruthSlice6ImmutabilityTests(unittest.TestCase):
    def test_material_rule_ground_truth_is_immutable(self) -> None:
        gt = _make_valid_material_rule_gt()
        with self.assertRaises(FrozenInstanceError):
            gt.material_id = "MAT-9999"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()

