"""Testes unitários do read-model de domínio CatalogQualityReport (Slice 1A)."""

import unittest
from dataclasses import FrozenInstanceError

from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import (
    GovernanceAssessment,
    GovernanceDecision,
)


def _make_assessment(
    material_id: str = "MAT-0001",
    *,
    completeness: float = 1.0,
    confidence: float = 1.0,
    decision: GovernanceDecision = GovernanceDecision.APPROVE,
) -> GovernanceAssessment:
    return GovernanceAssessment(
        material_id=material_id,
        completeness=completeness,
        confidence=confidence,
        decision=decision,
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


if __name__ == "__main__":
    unittest.main()
