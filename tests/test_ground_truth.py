from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.domain import GovernanceDecision, IssueType
from agent_lab.ground_truth import (
    DuplicatePairGroundTruth,
    LabelProvenance,
    MaterialRuleGroundTruth,
)
from agent_lab.human_review import HumanDecision, VerifiedSpecialistIdentity


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


class GroundTruthSlice7DuplicatePairNominalTests(unittest.TestCase):
    def test_duplicate_pair_ground_truth_synthetic_minimal_valid(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruth

        labeled_at = datetime(
            2026, 9, 10, 9, 0,
            tzinfo=timezone.utc,
        )

        gt = DuplicatePairGroundTruth(
            evaluation_case_id="CASE-DUP-001",
            ground_truth_id="GT-DUP-001",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
            is_duplicate=True,
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="SPEC-0115-DUP-FIXTURE-01",
            annotator=None,
            labeled_at=labeled_at,
            rationale="Registros representam a mesma entidade governada.",
        )

        self.assertEqual(gt.evaluation_case_id, "CASE-DUP-001")
        self.assertEqual(gt.ground_truth_id, "GT-DUP-001")
        self.assertEqual(gt.material_id_a, "MAT-1001")
        self.assertEqual(gt.material_id_b, "MAT-1002")
        self.assertTrue(gt.is_duplicate)
        self.assertEqual(gt.provenance, LabelProvenance.SYNTHETIC_SPECIFIED)
        self.assertEqual(gt.source_reference, "SPEC-0115-DUP-FIXTURE-01")
        self.assertIsNone(gt.annotator)
        self.assertEqual(gt.labeled_at, labeled_at)
        self.assertEqual(
            gt.rationale,
            "Registros representam a mesma entidade governada.",
        )


def _make_valid_duplicate_pair_gt(
    **overrides: object,
) -> DuplicatePairGroundTruth:
    kwargs: dict[str, object] = {
        "evaluation_case_id": "CASE-DUP-001",
        "ground_truth_id": "GT-DUP-001",
        "material_id_a": "MAT-1001",
        "material_id_b": "MAT-1002",
        "is_duplicate": True,
        "provenance": LabelProvenance.SYNTHETIC_SPECIFIED,
        "source_reference": "SPEC-0115-DUP-FIXTURE-01",
        "annotator": None,
        "labeled_at": datetime(
            2026, 9, 10, 9, 0,
            tzinfo=timezone.utc,
        ),
        "rationale": "Registros representam a mesma entidade governada.",
    }
    kwargs.update(overrides)
    return DuplicatePairGroundTruth(**kwargs)  # type: ignore[arg-type]


class GroundTruthSlice8DuplicatePairRelationalTests(unittest.TestCase):
    def test_is_duplicate_rejects_non_bool(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_duplicate_pair_gt(is_duplicate=1)

    def test_duplicate_pair_rejects_self_referential(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                material_id_a="MAT-1001",
                material_id_b="MAT-1001",
            )

    def test_duplicate_pair_rejects_reversed_order(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                material_id_a="MAT-1002",
                material_id_b="MAT-1001",
            )

    def test_duplicate_pair_accepts_false_duplicate(self) -> None:
        gt = _make_valid_duplicate_pair_gt(is_duplicate=False)
        self.assertFalse(gt.is_duplicate)


DUPLICATE_PAIR_TEXT_FIELDS = (
    "evaluation_case_id",
    "ground_truth_id",
    "material_id_a",
    "material_id_b",
    "source_reference",
    "rationale",
)


class GroundTruthSlice9DuplicatePairTextFieldsTests(unittest.TestCase):
    def test_duplicate_pair_text_fields_reject_non_str(self) -> None:
        for field in DUPLICATE_PAIR_TEXT_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    _make_valid_duplicate_pair_gt(**{field: 123})

    def test_duplicate_pair_text_fields_reject_empty_or_whitespace(self) -> None:
        for field in DUPLICATE_PAIR_TEXT_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    _make_valid_duplicate_pair_gt(**{field: "   "})

    def test_duplicate_pair_text_fields_stripped(self) -> None:
        gt = _make_valid_duplicate_pair_gt(
            evaluation_case_id="  CASE-DUP-001  ",
            ground_truth_id="  GT-DUP-001  ",
            material_id_a="  MAT-1001  ",
            material_id_b="  MAT-1002  ",
            source_reference="  SPEC-0115-DUP-FIXTURE-01  ",
            rationale="  Mesmo item cadastral.  ",
        )
        self.assertEqual(gt.evaluation_case_id, "CASE-DUP-001")
        self.assertEqual(gt.ground_truth_id, "GT-DUP-001")
        self.assertEqual(gt.material_id_a, "MAT-1001")
        self.assertEqual(gt.material_id_b, "MAT-1002")
        self.assertEqual(gt.source_reference, "SPEC-0115-DUP-FIXTURE-01")
        self.assertEqual(gt.rationale, "Mesmo item cadastral.")

    def test_duplicate_pair_normalization_before_relational_validation(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                material_id_a="  MAT-1001  ",
                material_id_b="MAT-1001",
            )


class GroundTruthSlice10DuplicatePairProvenanceAnnotatorTests(unittest.TestCase):
    def test_duplicate_pair_provenance_rejects_string_equivalent(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_duplicate_pair_gt(provenance="SYNTHETIC_SPECIFIED")

    def test_duplicate_pair_specialist_curated_rejects_none_annotator(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=None,
            )

    def test_duplicate_pair_specialist_curated_rejects_non_specialist_annotator(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_duplicate_pair_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator="SPEC-001",
            )

    def test_duplicate_pair_synthetic_specified_rejects_present_annotator(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                annotator=_make_verified_specialist(),
            )

    def test_duplicate_pair_specialist_curated_valid(self) -> None:
        specialist = _make_verified_specialist()
        gt = _make_valid_duplicate_pair_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
        )
        self.assertEqual(gt.provenance, LabelProvenance.SPECIALIST_CURATED)
        self.assertEqual(gt.annotator, specialist)


class GroundTruthSlice11DuplicatePairTemporalTests(unittest.TestCase):
    def test_duplicate_pair_labeled_at_rejects_non_datetime(self) -> None:
        with self.assertRaises(TypeError):
            _make_valid_duplicate_pair_gt(
                labeled_at="2026-09-10T09:00:00Z",
            )

    def test_duplicate_pair_labeled_at_rejects_naive_datetime(self) -> None:
        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                labeled_at=datetime(2026, 9, 10, 9, 0),
            )

    def test_duplicate_pair_specialist_verified_at_cannot_be_after_labeled_at(
        self,
    ) -> None:
        labeled_at = datetime(
            2026,
            9,
            10,
            9,
            0,
            tzinfo=timezone.utc,
        )
        specialist = _make_verified_specialist_at(
            datetime(
                2026,
                9,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            _make_valid_duplicate_pair_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=specialist,
                labeled_at=labeled_at,
            )

    def test_duplicate_pair_specialist_verified_at_equal_to_labeled_at_is_valid(
        self,
    ) -> None:
        timestamp = datetime(
            2026,
            9,
            10,
            9,
            0,
            tzinfo=timezone.utc,
        )
        specialist = _make_verified_specialist_at(timestamp)

        gt = _make_valid_duplicate_pair_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
            labeled_at=timestamp,
        )

        self.assertEqual(gt.labeled_at, timestamp)
        self.assertEqual(gt.annotator, specialist)


class GroundTruthSlice12DuplicatePairImmutabilityTests(unittest.TestCase):
    def test_duplicate_pair_ground_truth_is_immutable(self) -> None:
        gt = _make_valid_duplicate_pair_gt()
        with self.assertRaises(FrozenInstanceError):
            gt.material_id_a = "MAT-9999"  # type: ignore[misc]


class GroundTruthSlice13DecisionRecommendationNominalTests(unittest.TestCase):
    def test_decision_recommendation_ground_truth_synthetic_minimal_valid(
        self,
    ) -> None:
        from agent_lab.ground_truth import DecisionRecommendationGroundTruth

        gt = DecisionRecommendationGroundTruth(
            evaluation_case_id="CASE-DEC-001",
            ground_truth_id="GT-DEC-001",
            material_id="MAT-1001",
            expected_recommendation=GovernanceDecision.APPROVE,
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="synthetic://spec-0115/decision/001",
            annotator=None,
            labeled_at=datetime(
                2026,
                9,
                10,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            rationale="Synthetic governed recommendation reference.",
        )

        self.assertEqual(
            gt.expected_recommendation,
            GovernanceDecision.APPROVE,
        )
        self.assertEqual(
            gt.material_id,
            "MAT-1001",
        )
        self.assertEqual(
            gt.provenance,
            LabelProvenance.SYNTHETIC_SPECIFIED,
        )


class GroundTruthSlice14DecisionRecommendationExpectedRecommendationTests(unittest.TestCase):
    def test_expected_recommendation_rejects_string_equivalent(self) -> None:
        from agent_lab.ground_truth import DecisionRecommendationGroundTruth

        with self.assertRaises(TypeError):
            DecisionRecommendationGroundTruth(
                evaluation_case_id="CASE-DEC-001",
                ground_truth_id="GT-DEC-001",
                material_id="MAT-1001",
                expected_recommendation="APPROVE",
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="synthetic://spec-0115/decision/001",
                annotator=None,
                labeled_at=datetime(
                    2026,
                    9,
                    10,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
                rationale="Synthetic governed recommendation reference.",
            )

    def test_expected_recommendation_rejects_human_decision(self) -> None:
        from agent_lab.ground_truth import DecisionRecommendationGroundTruth

        with self.assertRaises(TypeError):
            DecisionRecommendationGroundTruth(
                evaluation_case_id="CASE-DEC-001",
                ground_truth_id="GT-DEC-001",
                material_id="MAT-1001",
                expected_recommendation=HumanDecision.APPROVE,
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                source_reference="synthetic://spec-0115/decision/001",
                annotator=None,
                labeled_at=datetime(
                    2026,
                    9,
                    10,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ),
                rationale="Synthetic governed recommendation reference.",
            )


def _make_valid_decision_recommendation_gt(
    **overrides: object,
):
    from agent_lab.ground_truth import DecisionRecommendationGroundTruth

    values: dict[str, object] = {
        "evaluation_case_id": "CASE-DEC-001",
        "ground_truth_id": "GT-DEC-001",
        "material_id": "MAT-1001",
        "expected_recommendation": GovernanceDecision.APPROVE,
        "provenance": LabelProvenance.SYNTHETIC_SPECIFIED,
        "source_reference": "synthetic://spec-0115/decision/001",
        "annotator": None,
        "labeled_at": datetime(
            2026,
            9,
            10,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        "rationale": "Synthetic governed recommendation reference.",
    }
    values.update(overrides)
    return DecisionRecommendationGroundTruth(**values)  # type: ignore[arg-type]


class GroundTruthSlice15DecisionRecommendationTextFieldsTests(unittest.TestCase):
    def test_decision_recommendation_text_fields_reject_non_str(self) -> None:
        field_names = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id",
            "source_reference",
            "rationale",
        )
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                with self.assertRaises(TypeError):
                    _make_valid_decision_recommendation_gt(
                        **{field_name: 123}
                    )

    def test_decision_recommendation_text_fields_reject_empty_or_whitespace(
        self,
    ) -> None:
        field_names = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id",
            "source_reference",
            "rationale",
        )
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    _make_valid_decision_recommendation_gt(
                        **{field_name: "   "}
                    )

    def test_decision_recommendation_text_fields_stripped(self) -> None:
        gt = _make_valid_decision_recommendation_gt(
            evaluation_case_id="  CASE-DEC-001  ",
            ground_truth_id="  GT-DEC-001  ",
            material_id="  MAT-1001  ",
            source_reference="  synthetic://spec-0115/decision/001  ",
            rationale="  Synthetic governed recommendation reference.  ",
        )
        self.assertEqual(
            gt.evaluation_case_id,
            "CASE-DEC-001",
        )
        self.assertEqual(
            gt.ground_truth_id,
            "GT-DEC-001",
        )
        self.assertEqual(
            gt.material_id,
            "MAT-1001",
        )
        self.assertEqual(
            gt.source_reference,
            "synthetic://spec-0115/decision/001",
        )
        self.assertEqual(
            gt.rationale,
            "Synthetic governed recommendation reference.",
        )


class GroundTruthSlice16DecisionRecommendationProvenanceAnnotatorTests(
    unittest.TestCase
):
    def test_decision_recommendation_provenance_rejects_string_equivalent(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            _make_valid_decision_recommendation_gt(
                provenance="SYNTHETIC_SPECIFIED",
            )

    def test_decision_recommendation_specialist_curated_rejects_none_annotator(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            _make_valid_decision_recommendation_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=None,
            )

    def test_decision_recommendation_specialist_curated_rejects_non_specialist_annotator(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            _make_valid_decision_recommendation_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator="SPEC-001",
            )

    def test_decision_recommendation_synthetic_specified_rejects_present_annotator(
        self,
    ) -> None:
        specialist = _make_verified_specialist_at(
            datetime(
                2026,
                9,
                10,
                8,
                0,
                tzinfo=timezone.utc,
            )
        )
        with self.assertRaises(ValueError):
            _make_valid_decision_recommendation_gt(
                provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
                annotator=specialist,
            )

    def test_decision_recommendation_specialist_curated_valid(self) -> None:
        specialist = _make_verified_specialist_at(
            datetime(
                2026,
                9,
                10,
                8,
                0,
                tzinfo=timezone.utc,
            )
        )
        gt = _make_valid_decision_recommendation_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
        )
        self.assertEqual(
            gt.provenance,
            LabelProvenance.SPECIALIST_CURATED,
        )
        self.assertEqual(
            gt.annotator,
            specialist,
        )


class GroundTruthSlice17DecisionRecommendationTemporalTests(
    unittest.TestCase
):
    def test_decision_recommendation_labeled_at_rejects_non_datetime(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            _make_valid_decision_recommendation_gt(
                labeled_at="2026-09-10T09:00:00Z",
            )

    def test_decision_recommendation_labeled_at_rejects_naive_datetime(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            _make_valid_decision_recommendation_gt(
                labeled_at=datetime(
                    2026,
                    9,
                    10,
                    9,
                    0,
                ),
            )

    def test_decision_recommendation_specialist_verified_at_cannot_be_after_labeled_at(
        self,
    ) -> None:
        labeled_at = datetime(
            2026,
            9,
            10,
            9,
            0,
            tzinfo=timezone.utc,
        )
        specialist = _make_verified_specialist_at(
            datetime(
                2026,
                9,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            )
        )
        with self.assertRaises(ValueError):
            _make_valid_decision_recommendation_gt(
                provenance=LabelProvenance.SPECIALIST_CURATED,
                annotator=specialist,
                labeled_at=labeled_at,
            )

    def test_decision_recommendation_specialist_verified_at_equal_to_labeled_at_is_valid(
        self,
    ) -> None:
        timestamp = datetime(
            2026,
            9,
            10,
            9,
            0,
            tzinfo=timezone.utc,
        )
        specialist = _make_verified_specialist_at(timestamp)
        gt = _make_valid_decision_recommendation_gt(
            provenance=LabelProvenance.SPECIALIST_CURATED,
            annotator=specialist,
            labeled_at=timestamp,
        )
        self.assertEqual(
            gt.labeled_at,
            timestamp,
        )
        self.assertEqual(
            gt.annotator,
            specialist,
        )


class GroundTruthSlice18DecisionRecommendationImmutabilityTests(
    unittest.TestCase
):
    def test_decision_recommendation_ground_truth_is_immutable(self) -> None:
        gt = _make_valid_decision_recommendation_gt()

        with self.assertRaises(FrozenInstanceError):
            gt.material_id = "MAT-9999"  # type: ignore[misc]


class GroundTruthSlice19PublicExportsTests(unittest.TestCase):
    def test_label_provenance_is_publicly_exported(self) -> None:
        from agent_lab import LabelProvenance as PublicLabelProvenance
        from agent_lab.ground_truth import (
            LabelProvenance as GroundTruthLabelProvenance,
        )

        self.assertIs(
            PublicLabelProvenance,
            GroundTruthLabelProvenance,
        )

    def test_material_rule_ground_truth_is_publicly_exported(self) -> None:
        from agent_lab import (
            MaterialRuleGroundTruth as PublicMaterialRuleGroundTruth,
        )
        from agent_lab.ground_truth import (
            MaterialRuleGroundTruth as GroundTruthMaterialRuleGroundTruth,
        )

        self.assertIs(
            PublicMaterialRuleGroundTruth,
            GroundTruthMaterialRuleGroundTruth,
        )

    def test_duplicate_pair_ground_truth_is_publicly_exported(self) -> None:
        from agent_lab import (
            DuplicatePairGroundTruth as PublicDuplicatePairGroundTruth,
        )
        from agent_lab.ground_truth import (
            DuplicatePairGroundTruth as GroundTruthDuplicatePairGroundTruth,
        )

        self.assertIs(
            PublicDuplicatePairGroundTruth,
            GroundTruthDuplicatePairGroundTruth,
        )

    def test_decision_recommendation_ground_truth_is_publicly_exported(
        self,
    ) -> None:
        from agent_lab import (
            DecisionRecommendationGroundTruth as PublicDecisionRecommendationGroundTruth,
        )
        from agent_lab.ground_truth import (
            DecisionRecommendationGroundTruth as GroundTruthDecisionRecommendationGroundTruth,
        )

        self.assertIs(
            PublicDecisionRecommendationGroundTruth,
            GroundTruthDecisionRecommendationGroundTruth,
        )


class MaterialRuleGroundTruthDatasetSlice1Tests(unittest.TestCase):
    def test_material_rule_ground_truth_dataset_import_and_empty_nominal(
        self,
    ) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(),
        )

        self.assertEqual(dataset.dataset_id, "DS-MATERIAL-RULES")
        self.assertEqual(dataset.items, ())

    def test_material_rule_ground_truth_dataset_normalizes_dataset_id_with_strip(
        self,
    ) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="   DS-MATERIAL-RULES   ",
            items=(),
        )

        self.assertEqual(dataset.dataset_id, "DS-MATERIAL-RULES")
        self.assertEqual(dataset.items, ())


class MaterialRuleGroundTruthDatasetSlice2Tests(unittest.TestCase):
    def test_dataset_id_rejects_non_str(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        invalid_ids = (123, None, ("DS-01",), ["DS-01"])
        for invalid_id in invalid_ids:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(TypeError):
                    MaterialRuleGroundTruthDataset(
                        dataset_id=invalid_id,  # type: ignore[arg-type]
                        items=(),
                    )

    def test_dataset_id_rejects_empty_or_whitespace(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        empty_ids = ("", "   ", "\t\n")
        for empty_id in empty_ids:
            with self.subTest(empty_id=empty_id):
                with self.assertRaises(ValueError):
                    MaterialRuleGroundTruthDataset(
                        dataset_id=empty_id,
                        items=(),
                    )

    def test_items_rejects_non_tuple_container(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        invalid_items = ([], set(), {}, "not-a-tuple", 123)
        for items_container in invalid_items:
            with self.subTest(items_container=items_container):
                with self.assertRaises(TypeError):
                    MaterialRuleGroundTruthDataset(
                        dataset_id="DS-MATERIAL-RULES",
                        items=items_container,  # type: ignore[arg-type]
                    )


class MaterialRuleGroundTruthDatasetSlice3Tests(unittest.TestCase):
    def test_items_accepts_valid_material_rule_ground_truth_instances(
        self,
    ) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt = _make_valid_material_rule_gt()
        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt,),
        )

        self.assertEqual(dataset.dataset_id, "DS-MATERIAL-RULES")
        self.assertEqual(dataset.items, (gt,))

    def test_items_rejects_non_material_rule_ground_truth_element(
        self,
    ) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        invalid_elements = (
            "invalid-item",
            object(),
            123,
            _make_valid_duplicate_pair_gt(),
        )
        for invalid_element in invalid_elements:
            with self.subTest(invalid_element=invalid_element):
                with self.assertRaises(TypeError):
                    MaterialRuleGroundTruthDataset(
                        dataset_id="DS-MATERIAL-RULES",
                        items=(invalid_element,),  # type: ignore[arg-type]
                    )

    def test_items_rejects_heterogeneous_tuple_with_valid_and_invalid_element(
        self,
    ) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        valid_gt = _make_valid_material_rule_gt()
        with self.assertRaises(TypeError):
            MaterialRuleGroundTruthDataset(
                dataset_id="DS-MATERIAL-RULES",
                items=(valid_gt, "invalid-element"),  # type: ignore[arg-type]
            )


class MaterialRuleGroundTruthDatasetSlice4Tests(unittest.TestCase):
    def test_items_accepts_multiple_distinct_items(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt1 = _make_valid_material_rule_gt(
            ground_truth_id="GT-001",
            evaluation_case_id="CASE-001",
            material_id="MAT-1001",
        )
        gt2 = _make_valid_material_rule_gt(
            ground_truth_id="GT-002",
            evaluation_case_id="CASE-002",
            material_id="MAT-1002",
        )

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt1, gt2),
        )

        self.assertEqual(dataset.dataset_id, "DS-MATERIAL-RULES")
        self.assertEqual(len(dataset.items), 2)
        self.assertIn(gt1, dataset.items)
        self.assertIn(gt2, dataset.items)

    def test_items_rejects_duplicate_ground_truth_id(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt1 = _make_valid_material_rule_gt(
            ground_truth_id="GT-SAME",
            evaluation_case_id="CASE-001",
            material_id="MAT-1001",
        )
        gt2 = _make_valid_material_rule_gt(
            ground_truth_id="GT-SAME",
            evaluation_case_id="CASE-002",
            material_id="MAT-1002",
        )

        with self.assertRaises(ValueError):
            MaterialRuleGroundTruthDataset(
                dataset_id="DS-MATERIAL-RULES",
                items=(gt1, gt2),
            )

    def test_items_rejects_duplicate_evaluation_case_id(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt1 = _make_valid_material_rule_gt(
            ground_truth_id="GT-001",
            evaluation_case_id="CASE-SAME",
            material_id="MAT-1001",
        )
        gt2 = _make_valid_material_rule_gt(
            ground_truth_id="GT-002",
            evaluation_case_id="CASE-SAME",
            material_id="MAT-1002",
        )

        with self.assertRaises(ValueError):
            MaterialRuleGroundTruthDataset(
                dataset_id="DS-MATERIAL-RULES",
                items=(gt1, gt2),
            )


class MaterialRuleGroundTruthDatasetSlice5Tests(unittest.TestCase):
    def test_out_of_order_input_is_normalized_to_canonical_order(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt_case_002 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-1002",
        )
        gt_case_001 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-1001",
        )

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt_case_002, gt_case_001),
        )

        self.assertEqual(
            dataset.items,
            (gt_case_001, gt_case_002),
        )

    def test_final_representation_is_independent_of_input_order(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt1 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id="MAT-1001",
        )
        gt2 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id="MAT-1002",
        )

        dataset_a = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt2, gt1),
        )
        dataset_b = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt1, gt2),
        )

        self.assertEqual(dataset_a.items, dataset_b.items)

    def test_canonical_ordering_by_composite_key(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt1 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-003",
            material_id="MAT-1001",
        )
        gt2 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-001",
            material_id="MAT-1002",
        )
        gt3 = _make_valid_material_rule_gt(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-002",
            material_id="MAT-1003",
        )

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt3, gt1, gt2),
        )

        expected_order = tuple(
            sorted(
                (gt3, gt1, gt2),
                key=lambda item: (item.evaluation_case_id, item.ground_truth_id),
            )
        )
        self.assertEqual(dataset.items, (gt1, gt2, gt3))
        self.assertEqual(dataset.items, expected_order)


class MaterialRuleGroundTruthDatasetSlice6Tests(unittest.TestCase):
    def test_dataset_id_cannot_be_mutated(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(),
        )

        with self.assertRaises(FrozenInstanceError):
            dataset.dataset_id = "OTHER"  # type: ignore[misc]

    def test_items_cannot_be_mutated(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        gt = _make_valid_material_rule_gt()
        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(gt,),
        )

        with self.assertRaises(FrozenInstanceError):
            dataset.items = ()  # type: ignore[misc]

    def test_slots_prevents_instance_dict(self) -> None:
        from agent_lab.ground_truth import MaterialRuleGroundTruthDataset

        dataset = MaterialRuleGroundTruthDataset(
            dataset_id="DS-MATERIAL-RULES",
            items=(),
        )

        self.assertFalse(hasattr(dataset, "__dict__"))


class MaterialRuleGroundTruthDatasetSlice7Tests(unittest.TestCase):
    def test_material_rule_ground_truth_dataset_public_import_and_identity(
        self,
    ) -> None:
        from agent_lab import MaterialRuleGroundTruthDataset as PublicDataset
        from agent_lab.ground_truth import (
            MaterialRuleGroundTruthDataset as ModuleDataset,
        )

        self.assertIs(PublicDataset, ModuleDataset)

    def test_material_rule_ground_truth_dataset_in_all(self) -> None:
        import agent_lab

        self.assertIn(
            "MaterialRuleGroundTruthDataset",
            agent_lab.__all__,
        )


class DuplicatePairGroundTruthDatasetBlock1Tests(unittest.TestCase):
    def test_nominal_empty_dataset(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(),
        )

        self.assertEqual(dataset.dataset_id, "DS-DUPLICATE-PAIRS")
        self.assertEqual(dataset.items, ())

    def test_dataset_id_normalized_with_strip(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="  DS-DUPLICATE-PAIRS  ",
            items=(),
        )

        self.assertEqual(dataset.dataset_id, "DS-DUPLICATE-PAIRS")

    def test_dataset_id_rejects_non_str(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        invalid_ids = (123, None, [], ())
        for invalid_id in invalid_ids:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(TypeError):
                    DuplicatePairGroundTruthDataset(
                        dataset_id=invalid_id,  # type: ignore[arg-type]
                        items=(),
                    )

    def test_dataset_id_rejects_empty_or_whitespace(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        empty_ids = ("", "   ", "\t\n")
        for empty_id in empty_ids:
            with self.subTest(empty_id=empty_id):
                with self.assertRaises(ValueError):
                    DuplicatePairGroundTruthDataset(
                        dataset_id=empty_id,
                        items=(),
                    )

    def test_items_rejects_non_tuple_container(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        invalid_containers = ([], set(), {}, "invalid", 123)
        for container in invalid_containers:
            with self.subTest(container=container):
                with self.assertRaises(TypeError):
                    DuplicatePairGroundTruthDataset(
                        dataset_id="DS-DUPLICATE-PAIRS",
                        items=container,  # type: ignore[arg-type]
                    )

    def test_items_accepts_valid_duplicate_pair_ground_truth(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt = _make_valid_duplicate_pair_gt()
        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt,),
        )

        self.assertEqual(dataset.dataset_id, "DS-DUPLICATE-PAIRS")
        self.assertEqual(dataset.items, (gt,))

    def test_items_rejects_non_duplicate_pair_ground_truth_element(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        invalid_elements = (
            object(),
            "invalid-item",
            123,
            _make_valid_material_rule_gt(),
        )
        for invalid_element in invalid_elements:
            with self.subTest(invalid_element=invalid_element):
                with self.assertRaises(TypeError):
                    DuplicatePairGroundTruthDataset(
                        dataset_id="DS-DUPLICATE-PAIRS",
                        items=(invalid_element,),  # type: ignore[arg-type]
                    )

    def test_items_rejects_heterogeneous_tuple(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        valid_gt = _make_valid_duplicate_pair_gt()
        with self.assertRaises(TypeError):
            DuplicatePairGroundTruthDataset(
                dataset_id="DS-DUPLICATE-PAIRS",
                items=(valid_gt, "invalid-element"),  # type: ignore[arg-type]
            )

    def test_immutability(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt = _make_valid_duplicate_pair_gt()
        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt,),
        )

        with self.assertRaises(FrozenInstanceError):
            dataset.dataset_id = "OTHER"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            dataset.items = ()  # type: ignore[misc]

    def test_slots_prevents_instance_dict(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(),
        )

        self.assertFalse(hasattr(dataset, "__dict__"))


class DuplicatePairGroundTruthDatasetBlock2Tests(unittest.TestCase):
    def test_multiple_distinct_items_accepted(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt1 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )
        gt2 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt1, gt2),
        )

        self.assertEqual(dataset.dataset_id, "DS-DUPLICATE-PAIRS")
        self.assertEqual(len(dataset.items), 2)
        self.assertIn(gt1, dataset.items)
        self.assertIn(gt2, dataset.items)

    def test_duplicate_ground_truth_id_rejected(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt1 = _make_valid_duplicate_pair_gt(
            ground_truth_id="GT-SAME",
            evaluation_case_id="CASE-001",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )
        gt2 = _make_valid_duplicate_pair_gt(
            ground_truth_id="GT-SAME",
            evaluation_case_id="CASE-002",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )

        with self.assertRaises(ValueError):
            DuplicatePairGroundTruthDataset(
                dataset_id="DS-DUPLICATE-PAIRS",
                items=(gt1, gt2),
            )

    def test_duplicate_evaluation_case_id_rejected(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt1 = _make_valid_duplicate_pair_gt(
            ground_truth_id="GT-001",
            evaluation_case_id="CASE-SAME",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )
        gt2 = _make_valid_duplicate_pair_gt(
            ground_truth_id="GT-002",
            evaluation_case_id="CASE-SAME",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )

        with self.assertRaises(ValueError):
            DuplicatePairGroundTruthDataset(
                dataset_id="DS-DUPLICATE-PAIRS",
                items=(gt1, gt2),
            )

    def test_out_of_order_input_normalized_to_canonical_order(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt_case_002 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )
        gt_case_001 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt_case_002, gt_case_001),
        )

        self.assertEqual(
            dataset.items,
            (gt_case_001, gt_case_002),
        )

    def test_representation_independent_of_input_order(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt1 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-001",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )
        gt2 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-002",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )

        dataset_a = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt2, gt1),
        )
        dataset_b = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt1, gt2),
        )

        self.assertEqual(dataset_a.items, dataset_b.items)

    def test_canonical_ordering_by_composite_key(self) -> None:
        from agent_lab.ground_truth import DuplicatePairGroundTruthDataset

        gt1 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-001",
            ground_truth_id="GT-003",
            material_id_a="MAT-1001",
            material_id_b="MAT-1002",
        )
        gt2 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-002",
            ground_truth_id="GT-001",
            material_id_a="MAT-1003",
            material_id_b="MAT-1004",
        )
        gt3 = _make_valid_duplicate_pair_gt(
            evaluation_case_id="CASE-003",
            ground_truth_id="GT-002",
            material_id_a="MAT-1005",
            material_id_b="MAT-1006",
        )

        dataset = DuplicatePairGroundTruthDataset(
            dataset_id="DS-DUPLICATE-PAIRS",
            items=(gt3, gt1, gt2),
        )

        expected_order = tuple(
            sorted(
                (gt3, gt1, gt2),
                key=lambda item: (item.evaluation_case_id, item.ground_truth_id),
            )
        )
        self.assertEqual(dataset.items, (gt1, gt2, gt3))
        self.assertEqual(dataset.items, expected_order)


class DuplicatePairGroundTruthDatasetBlock3Tests(unittest.TestCase):
    def test_public_import_and_identity(self) -> None:
        from agent_lab import (
            DuplicatePairGroundTruthDataset as PublicDataset,
        )
        from agent_lab.ground_truth import (
            DuplicatePairGroundTruthDataset as ModuleDataset,
        )

        self.assertIs(PublicDataset, ModuleDataset)

    def test_in_all(self) -> None:
        import agent_lab

        self.assertIn(
            "DuplicatePairGroundTruthDataset",
            agent_lab.__all__,
        )


if __name__ == "__main__":
    unittest.main()
