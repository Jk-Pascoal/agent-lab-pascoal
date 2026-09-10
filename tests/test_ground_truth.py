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


if __name__ == "__main__":
    unittest.main()
