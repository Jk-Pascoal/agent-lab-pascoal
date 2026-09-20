from datetime import datetime, timezone
import unittest

from agent_lab.domain import IssueType
from agent_lab.ground_truth import (
    LabelProvenance,
    MaterialRuleGroundTruth,
)
from agent_lab.ground_truth_serialization import (
    RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH,
    SCHEMA_VERSION_V1,
    material_rule_ground_truth_from_record,
    material_rule_ground_truth_to_record,
)
from agent_lab.human_review import VerifiedSpecialistIdentity


class MaterialRuleGroundTruthSerializationTests(unittest.TestCase):
    def _create_valid_record(
        self,
        *,
        provenance: str = LabelProvenance.SYNTHETIC_SPECIFIED.value,
        annotator: dict[str, object] | None = None,
    ) -> dict[str, object]:
        labeled_at = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
        return {
            "schema_version": 1,
            "record_type": RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH,
            "ground_truth_id": "GT-MR-001",
            "evaluation_case_id": "CASE-MR-001",
            "material_id": "MAT-100",
            "expected_issue_types": [
                IssueType.INVALID_UNIT.value,
                IssueType.MISSING_CRITICAL_FIELD.value,
            ],
            "provenance": provenance,
            "source_reference": "SYNTH-SPEC-V1",
            "annotator": annotator,
            "labeled_at": labeled_at.isoformat(),
            "rationale": "Synthetic rule test case with invalid unit and missing critical field",
        }

    def _create_valid_annotator(
        self,
        *,
        verified_at: str = "2026-09-15T08:30:00+00:00",
    ) -> dict[str, object]:
        return {
            "specialist_id": "SPEC-001",
            "identity_provider": "CORP_IDP",
            "identity_subject": "specialist.user@corp.example",
            "verification_id": "VER-999",
            "verified_at": verified_at,
        }

    # ==================================================
    # Testes Nominais e Constantes (Fases 1 e 2)
    # ==================================================

    def test_schema_version_and_record_type_constants(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)
        self.assertEqual(
            RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH,
            "MATERIAL_RULE_GROUND_TRUTH",
        )

    def test_round_trip_synthetic_specified(self) -> None:
        labeled_at = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
        gt = MaterialRuleGroundTruth(
            evaluation_case_id="CASE-MR-001",
            ground_truth_id="GT-MR-001",
            material_id="MAT-100",
            expected_issue_types=(
                IssueType.INVALID_UNIT,
                IssueType.MISSING_CRITICAL_FIELD,
            ),
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="SYNTH-SPEC-V1",
            annotator=None,
            labeled_at=labeled_at,
            rationale="Synthetic rule test case with invalid unit and missing critical field",
        )

        record = material_rule_ground_truth_to_record(gt)

        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(
            record["record_type"],
            "MATERIAL_RULE_GROUND_TRUTH",
        )
        self.assertEqual(record["ground_truth_id"], "GT-MR-001")
        self.assertEqual(record["evaluation_case_id"], "CASE-MR-001")
        self.assertEqual(record["material_id"], "MAT-100")
        self.assertIsInstance(record["expected_issue_types"], list)
        self.assertEqual(
            record["expected_issue_types"],
            sorted(
                [
                    IssueType.INVALID_UNIT.value,
                    IssueType.MISSING_CRITICAL_FIELD.value,
                ]
            ),
        )
        self.assertEqual(
            record["provenance"],
            LabelProvenance.SYNTHETIC_SPECIFIED.value,
        )
        self.assertIsNone(record["annotator"])
        self.assertEqual(record["labeled_at"], labeled_at.isoformat())
        self.assertEqual(record["source_reference"], "SYNTH-SPEC-V1")
        self.assertEqual(
            record["rationale"],
            "Synthetic rule test case with invalid unit and missing critical field",
        )

        reconstructed = material_rule_ground_truth_from_record(record)
        self.assertEqual(reconstructed, gt)
        self.assertEqual(
            reconstructed.expected_issue_types,
            gt.expected_issue_types,
        )
        self.assertIsNone(reconstructed.annotator)
        self.assertEqual(reconstructed.labeled_at, gt.labeled_at)

    def test_round_trip_specialist_curated(self) -> None:
        verified_at = datetime(2026, 9, 15, 8, 30, 0, tzinfo=timezone.utc)
        labeled_at = datetime(2026, 9, 20, 11, 0, 0, tzinfo=timezone.utc)

        specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist.user@corp.example",
            verification_id="VER-999",
            verified_at=verified_at,
        )

        gt = MaterialRuleGroundTruth(
            evaluation_case_id="CASE-MR-002",
            ground_truth_id="GT-MR-002",
            material_id="MAT-200",
            expected_issue_types=(IssueType.CLASSIFICATION_CONFLICT,),
            provenance=LabelProvenance.SPECIALIST_CURATED,
            source_reference="AUDIT-LOG-2026-09",
            annotator=specialist,
            labeled_at=labeled_at,
            rationale="Specialist curation after catalog audit",
        )

        record = material_rule_ground_truth_to_record(gt)

        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(
            record["record_type"],
            "MATERIAL_RULE_GROUND_TRUTH",
        )
        self.assertEqual(
            record["provenance"],
            LabelProvenance.SPECIALIST_CURATED.value,
        )
        self.assertIsInstance(record["annotator"], dict)
        annotator_record = record["annotator"]
        self.assertEqual(annotator_record["specialist_id"], "SPEC-001")
        self.assertEqual(annotator_record["identity_provider"], "CORP_IDP")
        self.assertEqual(
            annotator_record["identity_subject"],
            "specialist.user@corp.example",
        )
        self.assertEqual(annotator_record["verification_id"], "VER-999")
        self.assertEqual(
            annotator_record["verified_at"],
            verified_at.isoformat(),
        )

        reconstructed = material_rule_ground_truth_from_record(record)
        self.assertEqual(reconstructed, gt)
        self.assertEqual(reconstructed.annotator, specialist)
        self.assertEqual(
            reconstructed.annotator.verified_at,
            specialist.verified_at,
        )

    def test_expected_issue_types_canonical_ordering(self) -> None:
        issues = [
            IssueType.MISSING_CRITICAL_FIELD,
            IssueType.AMBIGUOUS_DESCRIPTION,
            IssueType.INVALID_UNIT,
        ]
        expected_sorted_values = sorted([i.value for i in issues])

        gt = MaterialRuleGroundTruth(
            evaluation_case_id="CASE-MR-003",
            ground_truth_id="GT-MR-003",
            material_id="MAT-300",
            expected_issue_types=tuple(issues),
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED,
            source_reference="ORDER-TEST-REF",
            annotator=None,
            labeled_at=datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc),
            rationale="Canonical ordering test rationale",
        )

        record = material_rule_ground_truth_to_record(gt)
        self.assertIsInstance(record["expected_issue_types"], list)
        self.assertEqual(
            record["expected_issue_types"],
            expected_sorted_values,
        )

    # ==================================================
    # 2. Closed-Schema Raiz
    # ==================================================

    def test_from_record_rejects_non_mapping_root(self) -> None:
        invalid_inputs = [None, "invalid_str", [1, 2], 123, True, False]
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(invalid_input)  # type: ignore[arg-type]

    def test_from_record_rejects_missing_required_root_field(self) -> None:
        record = self._create_valid_record()
        del record["material_id"]
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_unknown_root_field(self) -> None:
        record = self._create_valid_record()
        record["unexpected_field"] = "unexpected_value"
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_heterogeneous_unknown_root_keys(self) -> None:
        record = self._create_valid_record()
        record["unexpected_field"] = "unexpected_value"
        record[123] = "heterogeneous_key"  # type: ignore[index]
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    # ==================================================
    # 3. schema_version e record_type
    # ==================================================

    def test_from_record_rejects_invalid_schema_version(self) -> None:
        invalid_versions = [2, 0, "1", True, None]
        for invalid_version in invalid_versions:
            with self.subTest(invalid_version=invalid_version):
                record = self._create_valid_record()
                record["schema_version"] = invalid_version
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

        record_missing = self._create_valid_record()
        del record_missing["schema_version"]
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record_missing)

    def test_from_record_rejects_invalid_record_type(self) -> None:
        invalid_types = [
            "UNKNOWN_RECORD_TYPE",
            "DUPLICATE_PAIR_GROUND_TRUTH",
            "DECISION_RECOMMENDATION_GROUND_TRUTH",
            " MATERIAL_RULE_GROUND_TRUTH",
            "MATERIAL_RULE_GROUND_TRUTH ",
            None,
            True,
        ]
        for invalid_type in invalid_types:
            with self.subTest(invalid_type=invalid_type):
                record = self._create_valid_record()
                record["record_type"] = invalid_type
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    # ==================================================
    # 4. Strings Canônicas
    # ==================================================

    def test_from_record_rejects_non_canonical_strings(self) -> None:
        string_fields = [
            "ground_truth_id",
            "evaluation_case_id",
            "material_id",
            "source_reference",
            "rationale",
        ]
        invalid_string_values = [
            "",
            "   ",
            " valor",
            "valor ",
            "\tvalor",
            "valor\n",
            None,
            123,
            True,
        ]
        for field_name in string_fields:
            for invalid_val in invalid_string_values:
                with self.subTest(field=field_name, value=repr(invalid_val)):
                    record = self._create_valid_record()
                    record[field_name] = invalid_val
                    with self.assertRaises(ValueError):
                        material_rule_ground_truth_from_record(record)

    # ==================================================
    # 5. expected_issue_types
    # ==================================================

    def test_from_record_rejects_invalid_expected_issue_types(self) -> None:
        invalid_cases = [
            ("not_a_list_tuple", (IssueType.INVALID_UNIT.value,)),
            ("not_a_list_str", IssueType.INVALID_UNIT.value),
            ("not_a_list_int", 123),
            ("not_a_list_none", None),
            ("element_not_str", [123]),
            ("element_none", [None]),
            ("element_bool", [True]),
            ("unknown_enum", ["NON_EXISTENT_ISSUE_TYPE"]),
            ("possible_duplicate", [IssueType.POSSIBLE_DUPLICATE.value]),
            (
                "duplicate_elements",
                [
                    IssueType.INVALID_UNIT.value,
                    IssueType.INVALID_UNIT.value,
                ],
            ),
            (
                "out_of_canonical_order",
                [
                    IssueType.MISSING_CRITICAL_FIELD.value,
                    IssueType.INVALID_UNIT.value,
                ],
            ),
            (
                "leading_whitespace",
                [f" {IssueType.INVALID_UNIT.value}"],
            ),
            (
                "trailing_whitespace",
                [f"{IssueType.INVALID_UNIT.value} "],
            ),
        ]
        for label, invalid_value in invalid_cases:
            with self.subTest(case=label):
                record = self._create_valid_record()
                record["expected_issue_types"] = invalid_value
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    # ==================================================
    # 6. provenance / annotator
    # ==================================================

    def test_from_record_rejects_invalid_provenance(self) -> None:
        invalid_provenance_values = [
            "UNKNOWN_PROVENANCE",
            "",
            "   ",
            None,
            123,
            True,
        ]
        for invalid_val in invalid_provenance_values:
            with self.subTest(provenance=repr(invalid_val)):
                record = self._create_valid_record()
                record["provenance"] = invalid_val
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_synthetic_specified_with_annotator(self) -> None:
        record = self._create_valid_record(
            provenance=LabelProvenance.SYNTHETIC_SPECIFIED.value,
            annotator=self._create_valid_annotator(),
        )
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_specialist_curated_with_none_annotator(self) -> None:
        record = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=None,
        )
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_annotator_non_mapping(self) -> None:
        invalid_annotators = ["not_a_mapping", 123, True, [1, 2]]
        for invalid_annotator in invalid_annotators:
            with self.subTest(annotator=repr(invalid_annotator)):
                record = self._create_valid_record(
                    provenance=LabelProvenance.SPECIALIST_CURATED.value,
                    annotator=invalid_annotator,  # type: ignore[arg-type]
                )
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_annotator_missing_required_field(self) -> None:
        annotator = self._create_valid_annotator()
        del annotator["specialist_id"]
        record = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=annotator,
        )
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_annotator_unexpected_field(self) -> None:
        annotator = self._create_valid_annotator()
        annotator["extra_field"] = "extra_value"
        record = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=annotator,
        )
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_heterogeneous_unknown_annotator_keys(self) -> None:
        annotator = self._create_valid_annotator()
        annotator["unexpected_specialist_field"] = "unexpected_value"
        annotator[456] = "heterogeneous_key"  # type: ignore[index]
        record = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=annotator,
        )
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_specialist_non_canonical_strings(self) -> None:
        specialist_string_fields = [
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
        ]
        invalid_strings = [
            "",
            "   ",
            " valor",
            "valor ",
            "\tvalor",
            "valor\n",
            None,
            123,
            True,
        ]
        for field_name in specialist_string_fields:
            for invalid_val in invalid_strings:
                with self.subTest(field=field_name, value=repr(invalid_val)):
                    annotator = self._create_valid_annotator()
                    annotator[field_name] = invalid_val
                    record = self._create_valid_record(
                        provenance=LabelProvenance.SPECIALIST_CURATED.value,
                        annotator=annotator,
                    )
                    with self.assertRaises(ValueError):
                        material_rule_ground_truth_from_record(record)

    # ==================================================
    # 7. Temporalidade
    # ==================================================

    def test_from_record_rejects_invalid_labeled_at(self) -> None:
        invalid_timestamps = [
            "invalid_timestamp",
            "2026-09-20T10:00:00",  # naive (sem timezone)
            123456,
            None,
            True,
        ]
        for invalid_ts in invalid_timestamps:
            with self.subTest(labeled_at=repr(invalid_ts)):
                record = self._create_valid_record()
                record["labeled_at"] = invalid_ts
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    def test_from_record_rejects_invalid_annotator_verified_at(self) -> None:
        invalid_timestamps = [
            "invalid_timestamp",
            "2026-09-15T08:30:00",  # naive (sem timezone)
            123456,
            None,
            True,
        ]
        for invalid_ts in invalid_timestamps:
            with self.subTest(verified_at=repr(invalid_ts)):
                annotator = self._create_valid_annotator()
                annotator["verified_at"] = invalid_ts
                record = self._create_valid_record(
                    provenance=LabelProvenance.SPECIALIST_CURATED.value,
                    annotator=annotator,
                )
                with self.assertRaises(ValueError):
                    material_rule_ground_truth_from_record(record)

    def test_from_record_validates_temporal_relationship_between_verified_and_labeled(
        self,
    ) -> None:
        # verified_at > labeled_at deve falhar
        annotator = self._create_valid_annotator(
            verified_at="2026-09-20T12:00:00+00:00"
        )
        record = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=annotator,
        )
        record["labeled_at"] = "2026-09-20T10:00:00+00:00"
        with self.assertRaises(ValueError):
            material_rule_ground_truth_from_record(record)

        # verified_at == labeled_at deve ser aceito
        same_instant = "2026-09-20T10:00:00+00:00"
        annotator_equal = self._create_valid_annotator(
            verified_at=same_instant
        )
        record_equal = self._create_valid_record(
            provenance=LabelProvenance.SPECIALIST_CURATED.value,
            annotator=annotator_equal,
        )
        record_equal["labeled_at"] = same_instant
        obj = material_rule_ground_truth_from_record(record_equal)
        self.assertIsNotNone(obj.annotator)
        self.assertEqual(obj.annotator.verified_at, obj.labeled_at)

    # ==================================================
    # 8. Teste do to_record
    # ==================================================

    def test_to_record_rejects_non_material_rule_ground_truth_instance(
        self,
    ) -> None:
        invalid_inputs = [None, {}, "invalid_string", 123, True]
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(TypeError):
                    material_rule_ground_truth_to_record(invalid_input)  # type: ignore[arg-type]
