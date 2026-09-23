"""Testes unitários do read-model de domínio CatalogQualityReport (Slice 1A)."""

import unittest
from dataclasses import FrozenInstanceError
from types import MappingProxyType

from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import (
    GovernanceAssessment,
    GovernanceDecision,
    GovernanceIssue,
    IssueSeverity,
    IssueType,
)


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


if __name__ == "__main__":
    unittest.main()
