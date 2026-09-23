"""Testes unitários do read-model de domínio CatalogQualityReport (Slice 1A)."""

import unittest
from dataclasses import FrozenInstanceError
from itertools import permutations
from types import MappingProxyType

import agent_lab.catalog_quality as catalog_quality
from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import (
    GovernanceAssessment,
    GovernanceDecision,
    GovernanceIssue,
    IssueSeverity,
    IssueType,
    MaterialRecord,
)
from agent_lab.evidence import EvidenceSource
from agent_lab.validator import DeterministicGovernanceValidator


def _make_assessment(
    material_id: str = "MAT-0001",
    *,
    completeness: float = 1.0,
    confidence: float = 1.0,
    decision: GovernanceDecision = GovernanceDecision.APPROVE,
    issues: tuple[GovernanceIssue, ...] = (),
    duplicate_candidates: tuple[str, ...] = (),
) -> GovernanceAssessment:
    return GovernanceAssessment(
        material_id=material_id,
        completeness=completeness,
        confidence=confidence,
        decision=decision,
        issues=issues,
        duplicate_candidates=duplicate_candidates,
    )


class CatalogQualityReportSlice1ATests(unittest.TestCase):
    """Testes de construção básica e catálogo vazio (Slice 1A)."""

    def test_nominal_construction(self) -> None:
        report = CatalogQualityReport(
            catalog_id="CAT-2026-A",
            assessments=(),
        )
        self.assertEqual(report.catalog_id, "CAT-2026-A")
        self.assertEqual(report.assessments, ())

    def test_catalog_id_must_be_string(self) -> None:
        for invalid_id in [123, ["CAT-01"], None, {"id": "CAT-01"}]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(TypeError):
                    CatalogQualityReport(
                        catalog_id=invalid_id,  # type: ignore[arg-type]
                        assessments=(),
                    )

    def test_catalog_id_rejects_bool(self) -> None:
        for b in [True, False]:
            with self.subTest(b=b):
                with self.assertRaises(TypeError):
                    CatalogQualityReport(
                        catalog_id=b,  # type: ignore[arg-type]
                        assessments=(),
                    )

    def test_catalog_id_cannot_be_empty_or_whitespace(self) -> None:
        for empty_val in ["", "   ", "\t\n"]:
            with self.subTest(empty_val=repr(empty_val)):
                with self.assertRaises(ValueError):
                    CatalogQualityReport(
                        catalog_id=empty_val,
                        assessments=(),
                    )

    def test_catalog_id_is_stripped(self) -> None:
        report = CatalogQualityReport(
            catalog_id="  CAT-001-A  \n",
            assessments=(),
        )
        self.assertEqual(report.catalog_id, "CAT-001-A")

    def test_assessments_must_be_tuple(self) -> None:
        assessment = _make_assessment()
        for invalid_assessments in [
            [assessment],
            {assessment},
            (a for a in [assessment]),
            "not-a-tuple",
            123,
        ]:
            with self.subTest(invalid=type(invalid_assessments)):
                with self.assertRaises(TypeError):
                    CatalogQualityReport(
                        catalog_id="CAT-01",
                        assessments=invalid_assessments,  # type: ignore[arg-type]
                    )

    def test_assessments_items_must_be_governance_assessments(self) -> None:
        for invalid_item in ["not-an-assessment", 123, None, {}]:
            with self.subTest(invalid_item=invalid_item):
                with self.assertRaises(TypeError):
                    CatalogQualityReport(
                        catalog_id="CAT-01",
                        assessments=(invalid_item,),  # type: ignore[arg-type]
                    )

    def test_empty_catalog_metrics(self) -> None:
        report = CatalogQualityReport(
            catalog_id="CAT-EMPTY",
            assessments=(),
        )
        self.assertEqual(report.total_records, 0)
        self.assertTrue(report.is_empty)
        self.assertEqual(report.clean_records_count, 0)
        self.assertEqual(report.duplicate_pairs, ())
        self.assertEqual(report.duplicate_pairs_count, 0)
        self.assertIsNone(report.clean_records_ratio)
        self.assertIsNone(report.average_completeness)


class CatalogQualityReportSlice1BTests(unittest.TestCase):
    """Testes de imutabilidade e integridade estrutural/coleção de assessments (Slice 1B)."""

    # A. Imutabilidade estrutural
    def test_catalog_quality_report_is_frozen(self) -> None:
        report = CatalogQualityReport(catalog_id="CAT-01", assessments=())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            report.catalog_id = "CAT-OTHER"  # type: ignore[misc]

    def test_catalog_quality_report_has_slots(self) -> None:
        report = CatalogQualityReport(catalog_id="CAT-01", assessments=())
        self.assertFalse(hasattr(report, "__dict__"))
        self.assertTrue(hasattr(report, "__slots__"))
        with self.assertRaises((AttributeError, TypeError, FrozenInstanceError)):
            report.unexpected_attr = "value"  # type: ignore[attr-defined]

    # B. Integridade estrutural de assessment.material_id
    def test_assessment_material_id_rejects_non_string(self) -> None:
        for invalid_id in [123, ["MAT-001"], None]:
            with self.subTest(invalid_id=invalid_id):
                assessment = _make_assessment("MAT-001")
                object.__setattr__(assessment, "material_id", invalid_id)
                with self.assertRaises(TypeError):
                    CatalogQualityReport(catalog_id="CAT-01", assessments=(assessment,))

    def test_assessment_material_id_rejects_bool(self) -> None:
        for b in [True, False]:
            with self.subTest(b=b):
                assessment = _make_assessment("MAT-001")
                object.__setattr__(assessment, "material_id", b)
                with self.assertRaises(TypeError):
                    CatalogQualityReport(catalog_id="CAT-01", assessments=(assessment,))

    def test_assessment_material_id_cannot_be_empty_or_whitespace(self) -> None:
        for empty_id in ["", "   ", "\t\n"]:
            with self.subTest(empty_id=repr(empty_id)):
                assessment = _make_assessment("MAT-001")
                object.__setattr__(assessment, "material_id", empty_id)
                with self.assertRaises(ValueError):
                    CatalogQualityReport(catalog_id="CAT-01", assessments=(assessment,))

    def test_assessment_material_id_rejects_outer_whitespace(self) -> None:
        for padded_id in [" MAT-001", "MAT-001 ", "  MAT-001\n"]:
            with self.subTest(padded_id=repr(padded_id)):
                assessment = _make_assessment("MAT-001")
                object.__setattr__(assessment, "material_id", padded_id)
                with self.assertRaises(ValueError):
                    CatalogQualityReport(catalog_id="CAT-01", assessments=(assessment,))

    # C. Canonicalidade da coleção
    def test_assessments_must_be_sorted_by_material_id(self) -> None:
        a1 = _make_assessment("MAT-001")
        a2 = _make_assessment("MAT-002")
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a2, a1))

    def test_assessments_rejects_duplicate_material_id(self) -> None:
        a1 = _make_assessment("MAT-001")
        a2 = _make_assessment("MAT-001")
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))


class CatalogQualityReportSlice1CTests(unittest.TestCase):
    """Testes de integridade relacional de duplicate_candidates (Slice 1C)."""

    # A. Estrutura de duplicate_candidates
    def test_duplicate_candidates_must_be_tuple(self) -> None:
        a1 = _make_assessment("MAT-001")
        object.__setattr__(a1, "duplicate_candidates", ["MAT-002"])
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        with self.assertRaises(TypeError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    def test_duplicate_candidates_items_must_be_string(self) -> None:
        a1 = _make_assessment("MAT-001")
        object.__setattr__(a1, "duplicate_candidates", (123,))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        with self.assertRaises(TypeError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    def test_duplicate_candidates_structure_of_target_validated_before_symmetry(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002",))
        a2 = _make_assessment("MAT-002")
        object.__setattr__(a2, "duplicate_candidates", [])
        with self.assertRaises(TypeError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    def test_duplicate_candidates_elements_of_target_validated_before_symmetry(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002",))
        a2 = _make_assessment("MAT-002")
        object.__setattr__(a2, "duplicate_candidates", (123,))
        with self.assertRaises(TypeError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    # B. Integridade relacional
    def test_duplicate_candidates_rejects_self_reference(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-001",))
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1,))

    def test_duplicate_candidates_rejects_orphan_candidate(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-999",))
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1,))

    def test_duplicate_candidates_rejects_duplicates_internally(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002", "MAT-002"))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    def test_duplicate_candidates_must_be_sorted_lexicographically(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-003", "MAT-002"))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        a3 = _make_assessment("MAT-003", duplicate_candidates=("MAT-001",))
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2, a3))

    def test_duplicate_candidates_rejects_asymmetric_relation(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002",))
        a2 = _make_assessment("MAT-002", duplicate_candidates=())
        with self.assertRaises(ValueError):
            CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))

    # C. Caminho nominal relacional
    def test_duplicate_candidates_nominal_symmetric_relation(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002",))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        report = CatalogQualityReport(catalog_id="CAT-01", assessments=(a1, a2))
        self.assertEqual(report.duplicate_pairs, (("MAT-001", "MAT-002"),))
        self.assertEqual(report.duplicate_pairs_count, 1)


class CatalogQualityReportSlice1DATests(unittest.TestCase):
    """Testes de contagens escalares derivadas (Slice 1D-A)."""

    def test_empty_catalog_scalar_counts(self) -> None:
        report = CatalogQualityReport(catalog_id="CAT-EMPTY", assessments=())
        self.assertEqual(report.records_with_blocking_issues_count, 0)
        self.assertEqual(report.records_with_non_blocking_issues_count, 0)
        self.assertEqual(report.duplicate_candidate_records_count, 0)
        self.assertEqual(report.total_issues_count, 0)

    def test_blocking_issues_count_and_deduplication_per_record(self) -> None:
        issue_blocking_1 = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição obrigatória ausente",
            severity=IssueSeverity.BLOCKING,
        )
        issue_blocking_2 = GovernanceIssue(
            issue_type=IssueType.INVALID_UNIT,
            field_name="unit",
            message="unidade inválida",
            severity=IssueSeverity.BLOCKING,
        )
        a1 = _make_assessment(
            "MAT-001",
            issues=(issue_blocking_1, issue_blocking_2),
        )
        report = CatalogQualityReport(catalog_id="CAT-01", assessments=(a1,))
        self.assertEqual(report.records_with_blocking_issues_count, 1)
        self.assertEqual(report.records_with_non_blocking_issues_count, 0)
        self.assertEqual(report.total_issues_count, 2)

    def test_non_blocking_issues_count_only_warning_and_info(self) -> None:
        issue_warning = GovernanceIssue(
            issue_type=IssueType.SUSPICIOUS_UNIT,
            field_name="unit",
            message="unidade suspeita",
            severity=IssueSeverity.WARNING,
        )
        issue_info = GovernanceIssue(
            issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
            field_name="description_short",
            message="descrição curta",
            severity=IssueSeverity.INFO,
        )
        a1 = _make_assessment(
            "MAT-001",
            issues=(issue_warning, issue_info),
        )
        report = CatalogQualityReport(catalog_id="CAT-01", assessments=(a1,))
        self.assertEqual(report.records_with_blocking_issues_count, 0)
        self.assertEqual(report.records_with_non_blocking_issues_count, 1)
        self.assertEqual(report.total_issues_count, 2)

    def test_mixed_severities_catalog_counts(self) -> None:
        issue_blocking = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        issue_warning = GovernanceIssue(
            issue_type=IssueType.SUSPICIOUS_UNIT,
            field_name="unit",
            message="unidade suspeita",
            severity=IssueSeverity.WARNING,
        )
        issue_info = GovernanceIssue(
            issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
            field_name="description_short",
            message="descrição ambígua",
            severity=IssueSeverity.INFO,
        )

        a1_clean = _make_assessment("MAT-001")
        a2_blocking_and_warning = _make_assessment(
            "MAT-002",
            issues=(issue_blocking, issue_warning),
        )
        a3_non_blocking = _make_assessment(
            "MAT-003",
            issues=(issue_warning, issue_info),
        )

        report = CatalogQualityReport(
            catalog_id="CAT-MIXED",
            assessments=(a1_clean, a2_blocking_and_warning, a3_non_blocking),
        )
        self.assertEqual(report.records_with_blocking_issues_count, 1)
        self.assertEqual(report.records_with_non_blocking_issues_count, 1)
        self.assertEqual(report.total_issues_count, 4)

    def test_duplicate_candidate_records_count_counts_records_not_pairs(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002",))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        a3_clean = _make_assessment("MAT-003")

        report = CatalogQualityReport(
            catalog_id="CAT-DUP",
            assessments=(a1, a2, a3_clean),
        )
        self.assertEqual(report.duplicate_candidate_records_count, 2)
        self.assertEqual(report.duplicate_pairs_count, 1)


class CatalogQualityReportSlice1DBTests(unittest.TestCase):
    """Testes de distribuições derivadas e read-only (Slice 1D-B)."""

    def test_empty_catalog_distributions(self) -> None:
        report = CatalogQualityReport(catalog_id="CAT-EMPTY", assessments=())
        self.assertEqual(report.issues_by_severity, {})
        self.assertEqual(report.issues_by_type, {})
        self.assertIsInstance(report.issues_by_severity, MappingProxyType)
        self.assertIsInstance(report.issues_by_type, MappingProxyType)

    def test_issues_by_severity_distribution(self) -> None:
        issue_blocking = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        issue_warning_1 = GovernanceIssue(
            issue_type=IssueType.SUSPICIOUS_UNIT,
            field_name="unit",
            message="unidade suspeita 1",
            severity=IssueSeverity.WARNING,
        )
        issue_warning_2 = GovernanceIssue(
            issue_type=IssueType.INVALID_STATUS,
            field_name="status",
            message="status inválido",
            severity=IssueSeverity.WARNING,
        )
        issue_info = GovernanceIssue(
            issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
            field_name="description_short",
            message="descrição ambígua",
            severity=IssueSeverity.INFO,
        )

        a1 = _make_assessment(
            "MAT-001",
            issues=(issue_blocking, issue_warning_1),
        )
        a2 = _make_assessment(
            "MAT-002",
            issues=(issue_warning_2, issue_info),
        )
        a3_clean = _make_assessment("MAT-003")

        report = CatalogQualityReport(
            catalog_id="CAT-SEV",
            assessments=(a1, a2, a3_clean),
        )
        expected = {
            IssueSeverity.BLOCKING: 1,
            IssueSeverity.WARNING: 2,
            IssueSeverity.INFO: 1,
        }
        self.assertEqual(report.issues_by_severity, expected)

    def test_issues_by_type_distribution(self) -> None:
        issue_mcf_1 = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        issue_mcf_2 = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="unit",
            message="unidade ausente",
            severity=IssueSeverity.BLOCKING,
        )
        issue_unit = GovernanceIssue(
            issue_type=IssueType.SUSPICIOUS_UNIT,
            field_name="unit",
            message="unidade suspeita",
            severity=IssueSeverity.WARNING,
        )
        issue_desc = GovernanceIssue(
            issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
            field_name="description_short",
            message="descrição ambígua",
            severity=IssueSeverity.INFO,
        )

        a1 = _make_assessment(
            "MAT-001",
            issues=(issue_mcf_1, issue_unit),
        )
        a2 = _make_assessment(
            "MAT-002",
            issues=(issue_mcf_2, issue_desc),
        )

        report = CatalogQualityReport(
            catalog_id="CAT-TYPE",
            assessments=(a1, a2),
        )
        expected = {
            IssueType.MISSING_CRITICAL_FIELD: 2,
            IssueType.SUSPICIOUS_UNIT: 1,
            IssueType.AMBIGUOUS_DESCRIPTION: 1,
        }
        self.assertEqual(report.issues_by_type, expected)

    def test_distributions_are_read_only_mapping_proxies(self) -> None:
        issue = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        a1 = _make_assessment("MAT-001", issues=(issue,))
        report = CatalogQualityReport(catalog_id="CAT-RO", assessments=(a1,))

        by_severity = report.issues_by_severity
        by_type = report.issues_by_type

        self.assertIsInstance(by_severity, MappingProxyType)
        self.assertIsInstance(by_type, MappingProxyType)

        with self.assertRaises(TypeError):
            by_severity[IssueSeverity.INFO] = 99  # type: ignore[index]

        with self.assertRaises(TypeError):
            by_type[IssueType.AMBIGUOUS_DESCRIPTION] = 99  # type: ignore[index]


class CatalogQualityReportSlice1ETests(unittest.TestCase):
    """Testes de caracterização e hardening de métricas agregadas (Slice 1E)."""

    def test_populated_catalog_basic_metrics(self) -> None:
        issue = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        a1_clean = _make_assessment("MAT-001")
        a2_clean = _make_assessment("MAT-002")
        a3_with_issue = _make_assessment("MAT-003", issues=(issue,))

        report = CatalogQualityReport(
            catalog_id="CAT-POP",
            assessments=(a1_clean, a2_clean, a3_with_issue),
        )

        self.assertEqual(report.total_records, 3)
        self.assertFalse(report.is_empty)
        self.assertEqual(report.clean_records_count, 2)

    def test_clean_records_ratio_in_populated_catalog(self) -> None:
        issue = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="descrição ausente",
            severity=IssueSeverity.BLOCKING,
        )
        a1_clean = _make_assessment("MAT-001")
        a2_clean = _make_assessment("MAT-002")
        a3_with_issue = _make_assessment("MAT-003", issues=(issue,))

        report = CatalogQualityReport(
            catalog_id="CAT-RATIO",
            assessments=(a1_clean, a2_clean, a3_with_issue),
        )

        self.assertIsNotNone(report.clean_records_ratio)
        self.assertAlmostEqual(report.clean_records_ratio, 2 / 3)  # type: ignore[arg-type]

    def test_average_completeness_in_populated_catalog(self) -> None:
        a1 = _make_assessment("MAT-001", completeness=1.0)
        a2 = _make_assessment("MAT-002", completeness=0.5)
        a3 = _make_assessment("MAT-003", completeness=0.0)

        report = CatalogQualityReport(
            catalog_id="CAT-COMP",
            assessments=(a1, a2, a3),
        )

        self.assertIsNotNone(report.average_completeness)
        self.assertAlmostEqual(report.average_completeness, 0.5)  # type: ignore[arg-type]

    def test_multiple_duplicate_pairs_and_count(self) -> None:
        a1 = _make_assessment("MAT-001", duplicate_candidates=("MAT-002", "MAT-003"))
        a2 = _make_assessment("MAT-002", duplicate_candidates=("MAT-001",))
        a3 = _make_assessment("MAT-003", duplicate_candidates=("MAT-001",))

        report = CatalogQualityReport(
            catalog_id="CAT-MULTI-DUP",
            assessments=(a1, a2, a3),
        )

        expected_pairs = (
            ("MAT-001", "MAT-002"),
            ("MAT-001", "MAT-003"),
        )
        self.assertEqual(report.duplicate_pairs, expected_pairs)
        self.assertEqual(report.duplicate_pairs_count, 2)


class CatalogQualityPipelineSlice2ATests(unittest.TestCase):
    """Testes do pipeline de diagnóstico de catálogo: existência e entrada (Slice 2A)."""

    def test_empty_catalog(self) -> None:
        report = catalog_quality.diagnose_catalog_quality(
            (),
            catalog_id="CAT-EMPTY",
        )
        self.assertIsInstance(report, CatalogQualityReport)
        self.assertEqual(report.catalog_id, "CAT-EMPTY")
        self.assertEqual(report.assessments, ())
        self.assertEqual(report.total_records, 0)
        self.assertTrue(report.is_empty)

    def test_rejects_non_sequence_catalog(self) -> None:
        with self.assertRaises(TypeError):
            catalog_quality.diagnose_catalog_quality(
                123,  # type: ignore[arg-type]
                catalog_id="CAT-01",
            )

    def test_rejects_textual_pseudo_sequences(self) -> None:
        for invalid_seq in ["MAT-001", b"MAT-001", bytearray(b"MAT-001")]:
            with self.subTest(invalid_seq=type(invalid_seq)):
                with self.assertRaises(TypeError):
                    catalog_quality.diagnose_catalog_quality(
                        invalid_seq,  # type: ignore[arg-type]
                        catalog_id="CAT-01",
                    )

    def test_rejects_invalid_items_in_catalog(self) -> None:
        with self.assertRaises(TypeError):
            catalog_quality.diagnose_catalog_quality(
                (object(),),  # type: ignore[arg-type]
                catalog_id="CAT-01",
            )


class CatalogQualityPipelineSlice2BTests(unittest.TestCase):
    """Testes de invariantes de identidade de material_id e unicidade no catálogo (Slice 2B)."""

    def test_material_id_rejects_non_string(self) -> None:
        for invalid_id in [123, None, ["MAT-001"]]:
            with self.subTest(invalid_id=invalid_id):
                record = MaterialRecord(material_id="MAT-001")
                object.__setattr__(record, "material_id", invalid_id)
                with self.assertRaises(TypeError):
                    catalog_quality.diagnose_catalog_quality(
                        (record,),
                        catalog_id="CAT-01",
                    )

    def test_material_id_rejects_bool(self) -> None:
        for b in [True, False]:
            with self.subTest(b=b):
                record = MaterialRecord(material_id="MAT-001")
                object.__setattr__(record, "material_id", b)
                with self.assertRaises(TypeError):
                    catalog_quality.diagnose_catalog_quality(
                        (record,),
                        catalog_id="CAT-01",
                    )

    def test_material_id_rejects_empty_whitespace_and_outer_whitespace(self) -> None:
        for empty_or_padded in ["", "   ", "\t\n", " MAT-001", "MAT-001 "]:
            with self.subTest(material_id=repr(empty_or_padded)):
                record = MaterialRecord(material_id=empty_or_padded)
                with self.assertRaises(ValueError):
                    catalog_quality.diagnose_catalog_quality(
                        (record,),
                        catalog_id="CAT-01",
                    )

    def test_rejects_duplicate_material_id(self) -> None:
        record_a = MaterialRecord(material_id="MAT-001")
        record_b = MaterialRecord(material_id="MAT-001")
        with self.assertRaises(ValueError) as ctx:
            catalog_quality.diagnose_catalog_quality(
                (record_a, record_b),
                catalog_id="CAT-01",
            )

        self.assertEqual(
            str(ctx.exception),
            "duplicate material_id in catalog: 'MAT-001'",
        )


class CatalogQualityPipelineSlice2CTests(unittest.TestCase):
    """Testes do contrato de catalog_id no pipeline de diagnóstico (Slice 2C)."""

    def test_catalog_id_rejects_non_string(self) -> None:
        for invalid_id in [123, None, []]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(TypeError):
                    catalog_quality.diagnose_catalog_quality(
                        (),
                        catalog_id=invalid_id,  # type: ignore[arg-type]
                    )

    def test_catalog_id_rejects_bool(self) -> None:
        for b in [True, False]:
            with self.subTest(b=b):
                with self.assertRaises(TypeError):
                    catalog_quality.diagnose_catalog_quality(
                        (),
                        catalog_id=b,  # type: ignore[arg-type]
                    )

    def test_catalog_id_empty_whitespace_and_stripping(self) -> None:
        for empty_val in ["", "   ", "\t\n"]:
            with self.subTest(empty_val=repr(empty_val)):
                with self.assertRaises(ValueError):
                    catalog_quality.diagnose_catalog_quality(
                        (),
                        catalog_id=empty_val,
                    )

        report = catalog_quality.diagnose_catalog_quality(
            (),
            catalog_id="  CAT-01  ",
        )
        self.assertEqual(report.catalog_id, "CAT-01")

    def test_catalog_id_validation_precedes_non_empty_analysis(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        cases = (
            (123, TypeError),
            (None, TypeError),
            ([], TypeError),
            (True, TypeError),
            (False, TypeError),
            ("", ValueError),
            ("   ", ValueError),
            ("\t\n", ValueError),
        )

        for invalid_id, expected_exception in cases:
            with self.subTest(invalid_id=repr(invalid_id)):
                with self.assertRaises(expected_exception):
                    catalog_quality.diagnose_catalog_quality(
                        (record,),
                        catalog_id=invalid_id,  # type: ignore[arg-type]
                    )


class CatalogQualityPipelineSlice2DTests(unittest.TestCase):
    """Testes do pipeline de diagnóstico com catálogo unitário não-vazio (Slice 2D)."""

    def test_single_record_catalog_is_analyzed(self) -> None:
        record = MaterialRecord(
            material_id="MAT-001",
            description_short="PARAFUSO ACO",
            unit="UN",
        )
        expected = DeterministicGovernanceValidator().analyze(
            record,
            [],
        )
        report = catalog_quality.diagnose_catalog_quality(
            (record,),
            catalog_id="  CAT-01  ",
        )
        self.assertIsInstance(report, CatalogQualityReport)
        self.assertEqual(report.catalog_id, "CAT-01")
        self.assertEqual(report.total_records, 1)
        self.assertEqual(report.assessments, (expected,))


class CatalogQualityPipelineSlice2EATests(unittest.TestCase):
    """Testes do pipeline de diagnóstico com catálogo multi-registro fechado (Slice 2E-A)."""

    def test_two_record_catalog_is_sorted_and_analyzed_against_all_others(self) -> None:
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="PARAFUSO ACO 10 20",
            unit="UN",
        )
        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="ROLAMENTO SKF 30 40",
            unit="UN",
        )
        validator = DeterministicGovernanceValidator()
        expected_a = validator.analyze(
            record_a,
            [record_b],
        )
        expected_b = validator.analyze(
            record_b,
            [record_a],
        )
        report = catalog_quality.diagnose_catalog_quality(
            (record_b, record_a),
            catalog_id="CAT-02",
        )
        self.assertEqual(report.catalog_id, "CAT-02")
        self.assertEqual(report.total_records, 2)
        self.assertEqual(
            tuple(a.material_id for a in report.assessments),
            ("MAT-001", "MAT-002"),
        )
        self.assertEqual(
            report.assessments,
            (expected_a, expected_b),
        )


class CatalogQualityPipelineSlice2EBTests(unittest.TestCase):
    """Testes de simetria de duplicidade e evidências no pipeline (Slice 2E-B)."""

    def test_duplicate_relationship_is_symmetric_with_duplicate_evidence(self) -> None:
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="ROLAMENTO INDUSTRIAL A",
            unit="UN",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )
        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="ROLAMENTO INDUSTRIAL B",
            unit="UN",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )

        report = catalog_quality.diagnose_catalog_quality(
            (record_b, record_a),
            catalog_id="CAT-DUP",
        )

        assessment_a, assessment_b = report.assessments

        self.assertEqual(assessment_a.material_id, "MAT-001")
        self.assertEqual(assessment_b.material_id, "MAT-002")

        self.assertEqual(
            assessment_a.duplicate_candidates,
            ("MAT-002",),
        )
        self.assertEqual(
            assessment_b.duplicate_candidates,
            ("MAT-001",),
        )

        self.assertTrue(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in assessment_a.issues
            )
        )
        self.assertTrue(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in assessment_b.issues
            )
        )

        self.assertIsNotNone(assessment_a.evidence_collection)
        self.assertIsNotNone(assessment_b.evidence_collection)

        assert assessment_a.evidence_collection is not None
        assert assessment_b.evidence_collection is not None

        self.assertTrue(
            any(
                evidence.source is EvidenceSource.DUPLICATE
                and evidence.issue_type is IssueType.POSSIBLE_DUPLICATE
                for evidence in assessment_a.evidence_collection.evidence
            )
        )
        self.assertTrue(
            any(
                evidence.source is EvidenceSource.DUPLICATE
                and evidence.issue_type is IssueType.POSSIBLE_DUPLICATE
                for evidence in assessment_b.evidence_collection.evidence
            )
        )

        self.assertEqual(
            report.duplicate_pairs,
            (("MAT-001", "MAT-002"),),
        )
        self.assertEqual(report.duplicate_pairs_count, 1)


class CatalogQualityPipelineSlice2ECTests(unittest.TestCase):
    """Testes de invariância à ordem física de entrada no pipeline (Slice 2E-C)."""

    def test_report_is_invariant_to_catalog_input_order(self) -> None:
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="ROLAMENTO INDUSTRIAL A",
            unit="UN",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )
        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="ROLAMENTO INDUSTRIAL B",
            unit="UN",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )
        record_c = MaterialRecord(
            material_id="MAT-003",
            description_short="CORREIA INDUSTRIAL 30 40",
            unit="UN",
            manufacturer="GATES",
            manufacturer_part_number="A-999",
        )

        expected = catalog_quality.diagnose_catalog_quality(
            (record_a, record_b, record_c),
            catalog_id="CAT-ORDER",
        )

        self.assertEqual(
            tuple(
                assessment.material_id
                for assessment in expected.assessments
            ),
            ("MAT-001", "MAT-002", "MAT-003"),
        )
        self.assertEqual(
            expected.duplicate_pairs,
            (("MAT-001", "MAT-002"),),
        )

        for permuted_catalog in permutations(
            (record_a, record_b, record_c)
        ):
            with self.subTest(
                order=tuple(record.material_id for record in permuted_catalog)
            ):
                actual = catalog_quality.diagnose_catalog_quality(
                    permuted_catalog,
                    catalog_id="CAT-ORDER",
                )
                self.assertEqual(actual, expected)


class CatalogQualityPipelineSlice2EDTests(unittest.TestCase):
    """Testes de catálogo limpo e violações determinísticas no pipeline (Slice 2E-D)."""

    def test_clean_catalog_produces_approved_assessments_without_issues(self) -> None:
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="PARAFUSO SEXTAVADO M10",
            unit="UN",
            status="ACTIVE",
        )
        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="PORCA SEXTAVADA M10",
            unit="UN",
            status="ACTIVE",
        )

        report = catalog_quality.diagnose_catalog_quality(
            (record_b, record_a),
            catalog_id="CAT-CLEAN",
        )

        self.assertEqual(report.total_records, 2)
        self.assertEqual(
            tuple(a.material_id for a in report.assessments),
            ("MAT-001", "MAT-002"),
        )
        self.assertEqual(report.clean_records_count, 2)
        self.assertEqual(report.records_with_blocking_issues_count, 0)
        self.assertEqual(report.records_with_non_blocking_issues_count, 0)
        self.assertEqual(report.duplicate_pairs, ())

        for assessment in report.assessments:
            with self.subTest(material_id=assessment.material_id):
                self.assertIs(
                    assessment.decision,
                    GovernanceDecision.APPROVE,
                )
                self.assertEqual(assessment.issues, ())
                self.assertEqual(assessment.duplicate_candidates, ())

    def test_catalog_surfaces_deterministic_rule_violations(self) -> None:
        record = MaterialRecord(
            material_id="MAT-ERR",
            description_short="",
            unit="INVALID",
            status="BROKEN",
        )

        report = catalog_quality.diagnose_catalog_quality(
            (record,),
            catalog_id="CAT-RULES",
        )

        assessment = report.assessments[0]
        issue_types = tuple(
            issue.issue_type
            for issue in assessment.issues
        )

        self.assertIn(
            IssueType.MISSING_CRITICAL_FIELD,
            issue_types,
        )
        self.assertIn(
            IssueType.INVALID_UNIT,
            issue_types,
        )
        self.assertIn(
            IssueType.INVALID_STATUS,
            issue_types,
        )

        self.assertIs(
            assessment.decision,
            GovernanceDecision.REJECT,
        )
        self.assertEqual(report.records_with_blocking_issues_count, 1)
        self.assertEqual(report.clean_records_count, 0)


class CatalogQualityPipelineSlice2EETests(unittest.TestCase):
    """Testes de caracterização do comportamento sequencial legado de analyze_all() (Slice 2E-E)."""

    def test_analyze_all_preserves_legacy_sequential_duplicate_behavior(self) -> None:
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="ROLAMENTO INDUSTRIAL A",
            unit="UN",
            status="ACTIVE",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )

        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="ROLAMENTO INDUSTRIAL B",
            unit="UN",
            status="ACTIVE",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )

        assessments = DeterministicGovernanceValidator().analyze_all(
            [record_a, record_b]
        )

        self.assertEqual(len(assessments), 2)
        self.assertEqual(
            tuple(a.material_id for a in assessments),
            ("MAT-001", "MAT-002"),
        )

        self.assertEqual(
            assessments[0].duplicate_candidates,
            (),
        )
        self.assertEqual(
            assessments[1].duplicate_candidates,
            ("MAT-001",),
        )

        self.assertFalse(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in assessments[0].issues
            )
        )
        self.assertTrue(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in assessments[1].issues
            )
        )


if __name__ == "__main__":
    unittest.main()
