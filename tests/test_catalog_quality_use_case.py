import unittest

from agent_lab.catalog_quality import (
    CatalogQualityReport,
    diagnose_catalog_quality,
)
from agent_lab.catalog_quality_use_case import (
    CatalogDiagnosticPipeline,
    DiagnoseCatalogQualityUseCase,
)
from agent_lab.domain import IssueType, MaterialRecord


class _PermissivePipeline:
    def __init__(self) -> None:
        self.called = False
        self.received_catalog_id: str | None = None

    def __call__(
        self,
        catalog,
        *,
        catalog_id,
    ) -> CatalogQualityReport:
        self.called = True
        self.received_catalog_id = catalog_id
        return CatalogQualityReport(
            catalog_id=catalog_id,
            assessments=(),
        )


class _StaticResultPipeline:
    def __init__(self, result) -> None:
        self.result = result
        self.called = False

    def __call__(
        self,
        catalog,
        *,
        catalog_id,
    ):
        self.called = True
        return self.result


class _FailingPipeline:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.called = False

    def __call__(
        self,
        catalog,
        *,
        catalog_id,
    ):
        self.called = True
        raise self.error


class DiagnoseCatalogQualityUseCaseSlice3ATests(unittest.TestCase):
    def test_default_pipeline_executes_empty_catalog(self) -> None:
        use_case = DiagnoseCatalogQualityUseCase()

        result = use_case.execute(
            (),
            catalog_id="  CAT-APP  ",
        )

        self.assertIsInstance(result, CatalogQualityReport)
        self.assertEqual(result.catalog_id, "CAT-APP")
        self.assertEqual(result.assessments, ())
        self.assertEqual(result.total_records, 0)
        self.assertTrue(result.is_empty)


class DiagnoseCatalogQualityUseCaseSlice3BTests(unittest.TestCase):
    def test_rejects_non_sequence_catalog_before_pipeline(self) -> None:
        pipeline = _PermissivePipeline()
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        with self.assertRaises(TypeError):
            use_case.execute(
                123,  # type: ignore[arg-type]
                catalog_id="CAT-01",
            )

        self.assertFalse(pipeline.called)

    def test_rejects_textual_pseudo_sequences_before_pipeline(self) -> None:
        for invalid_seq in ["MAT-001", b"MAT-001", bytearray(b"MAT-001")]:
            with self.subTest(invalid_seq=type(invalid_seq)):
                pipeline = _PermissivePipeline()
                use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

                with self.assertRaises(TypeError):
                    use_case.execute(
                        invalid_seq,  # type: ignore[arg-type]
                        catalog_id="CAT-01",
                    )

                self.assertFalse(pipeline.called)

    def test_rejects_invalid_catalog_item_before_pipeline(self) -> None:
        pipeline = _PermissivePipeline()
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        with self.assertRaises(TypeError):
            use_case.execute(
                (object(),),  # type: ignore[arg-type]
                catalog_id="CAT-01",
            )

        self.assertFalse(pipeline.called)

    def test_rejects_invalid_catalog_id_before_pipeline(self) -> None:
        catalog = (
            MaterialRecord(material_id="MAT-001"),
        )
        cases = (
            (123, TypeError),
            (None, TypeError),
            (True, TypeError),
            (False, TypeError),
            ("", ValueError),
            ("   ", ValueError),
            ("\t\n", ValueError),
        )

        for invalid_id, expected_exception in cases:
            with self.subTest(invalid_id=repr(invalid_id)):
                pipeline = _PermissivePipeline()
                use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

                with self.assertRaises(expected_exception):
                    use_case.execute(
                        catalog,
                        catalog_id=invalid_id,  # type: ignore[arg-type]
                    )

                self.assertFalse(pipeline.called)

    def test_canonicalizes_catalog_id_before_pipeline(self) -> None:
        pipeline = _PermissivePipeline()
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        result = use_case.execute(
            (),
            catalog_id="  CAT-01  ",
        )

        self.assertTrue(pipeline.called)
        self.assertEqual(
            pipeline.received_catalog_id,
            "CAT-01",
        )
        self.assertIsInstance(result, CatalogQualityReport)


class DiagnoseCatalogQualityUseCaseSlice3CTests(unittest.TestCase):
    def test_rejects_non_catalog_quality_report_result(self) -> None:
        pipeline = _StaticResultPipeline(object())
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        with self.assertRaises(TypeError):
            use_case.execute(
                (),
                catalog_id="CAT-01",
            )

        self.assertTrue(pipeline.called)

    def test_rejects_mismatched_catalog_id(self) -> None:
        invalid_result = CatalogQualityReport(
            catalog_id="OTHER-CATALOG",
            assessments=(),
        )
        pipeline = _StaticResultPipeline(invalid_result)
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        with self.assertRaises(ValueError):
            use_case.execute(
                (),
                catalog_id="CAT-01",
            )

        self.assertTrue(pipeline.called)

    def test_rejects_mismatched_assessment_identities(self) -> None:
        cases = (
            (
                "missing",
                (
                    MaterialRecord(material_id="MAT-001"),
                    MaterialRecord(material_id="MAT-002"),
                ),
                diagnose_catalog_quality(
                    (MaterialRecord(material_id="MAT-001"),),
                    catalog_id="CAT-01",
                ),
            ),
            (
                "extra",
                (
                    MaterialRecord(material_id="MAT-001"),
                ),
                diagnose_catalog_quality(
                    (
                        MaterialRecord(material_id="MAT-001"),
                        MaterialRecord(material_id="MAT-002"),
                    ),
                    catalog_id="CAT-01",
                ),
            ),
            (
                "divergent",
                (
                    MaterialRecord(material_id="MAT-001"),
                ),
                diagnose_catalog_quality(
                    (MaterialRecord(material_id="MAT-999"),),
                    catalog_id="CAT-01",
                ),
            ),
        )

        for scenario, catalog, fake_result in cases:
            with self.subTest(scenario=scenario):
                pipeline = _StaticResultPipeline(fake_result)
                use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

                with self.assertRaises(ValueError):
                    use_case.execute(
                        catalog,
                        catalog_id="CAT-01",
                    )

                self.assertTrue(pipeline.called)

    def test_accepts_valid_injected_result(self) -> None:
        catalog = (
            MaterialRecord(material_id="MAT-002"),
            MaterialRecord(material_id="MAT-001"),
        )
        expected = diagnose_catalog_quality(
            catalog,
            catalog_id="CAT-01",
        )
        pipeline = _StaticResultPipeline(expected)
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        result = use_case.execute(
            catalog,
            catalog_id="CAT-01",
        )

        self.assertIs(result, expected)
        self.assertTrue(pipeline.called)


class DiagnoseCatalogQualityUseCaseSlice3DTests(unittest.TestCase):
    def test_pipeline_exception_propagates_unchanged(self) -> None:
        error = RuntimeError("pipeline failure")
        pipeline = _FailingPipeline(error)
        use_case = DiagnoseCatalogQualityUseCase(pipeline=pipeline)

        with self.assertRaises(RuntimeError) as context:
            use_case.execute(
                (),
                catalog_id="CAT-01",
            )

        self.assertTrue(pipeline.called)
        self.assertIs(context.exception, error)


class DiagnoseCatalogQualityUseCaseSlice3ETests(unittest.TestCase):
    def test_end_to_end_representative_industrial_catalog(self) -> None:
        record_c = MaterialRecord(
            material_id="MAT-003",
            description_short="PARAFUSO ACO",
            unit="INVALID",
            status="ACTIVE",
        )
        record_b = MaterialRecord(
            material_id="MAT-002",
            description_short="ROLAMENTO INDUSTRIAL B",
            unit="UN",
            status="ACTIVE",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )
        record_a = MaterialRecord(
            material_id="MAT-001",
            description_short="ROLAMENTO INDUSTRIAL A",
            unit="UN",
            status="ACTIVE",
            manufacturer="SKF",
            manufacturer_part_number="6205-ZZ",
        )

        catalog = (record_c, record_b, record_a)

        use_case = DiagnoseCatalogQualityUseCase()
        result = use_case.execute(
            catalog,
            catalog_id="  CAT-INDUSTRIAL-01  ",
        )

        self.assertIsInstance(result, CatalogQualityReport)
        self.assertEqual(result.catalog_id, "CAT-INDUSTRIAL-01")
        self.assertEqual(result.total_records, 3)

        self.assertEqual(
            tuple(
                assessment.material_id
                for assessment in result.assessments
            ),
            (
                "MAT-001",
                "MAT-002",
                "MAT-003",
            ),
        )

        self.assertEqual(
            result.duplicate_pairs,
            (
                ("MAT-001", "MAT-002"),
            ),
        )
        self.assertEqual(result.duplicate_pairs_count, 1)

        self.assertTrue(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in result.assessments[0].issues
            )
        )
        self.assertTrue(
            any(
                issue.issue_type is IssueType.POSSIBLE_DUPLICATE
                for issue in result.assessments[1].issues
            )
        )

        self.assertTrue(
            any(
                issue.issue_type is IssueType.INVALID_UNIT
                for issue in result.assessments[2].issues
            )
        )

        self.assertGreater(result.total_issues_count, 0)
        self.assertGreater(result.records_with_blocking_issues_count, 0)


class DiagnoseCatalogQualityUseCaseSlice3FTests(unittest.TestCase):
    def test_issue_149_symbols_are_exported_from_package_root(self) -> None:
        from agent_lab import (
            CatalogDiagnosticPipeline as ExportedCatalogDiagnosticPipeline,
            CatalogQualityReport as ExportedCatalogQualityReport,
            DiagnoseCatalogQualityUseCase as ExportedDiagnoseCatalogQualityUseCase,
            diagnose_catalog_quality as exported_diagnose_catalog_quality,
        )

        self.assertIs(
            ExportedCatalogDiagnosticPipeline,
            CatalogDiagnosticPipeline,
        )
        self.assertIs(
            ExportedDiagnoseCatalogQualityUseCase,
            DiagnoseCatalogQualityUseCase,
        )
        self.assertIs(
            ExportedCatalogQualityReport,
            CatalogQualityReport,
        )
        self.assertIs(
            exported_diagnose_catalog_quality,
            diagnose_catalog_quality,
        )


if __name__ == "__main__":
    unittest.main()
