"""End-to-end characterizations of #225 without changing the legacy scorer."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_quality import diagnose_catalog_quality
from agent_lab.dimension_candidate_audit import audit_dimension_candidates, main
from agent_lab.domain import MaterialRecord


def _material(material_id: str, description: str) -> MaterialRecord:
    return MaterialRecord(
        material_id=material_id,
        description_short=description,
        unit="PC",
        material_group="FIXADORES",
        status="ACTIVE",
    )


class DimensionCandidateAuditTests(unittest.TestCase):
    def _audit(self, first: str, second: str, *, schema_version: str = "v1") -> dict[str, object]:
        records = (_material("MAT-A", first), _material("MAT-B", second))
        report = diagnose_catalog_quality(records, catalog_id="DIM-SYNTHETIC")
        self.assertEqual(report.duplicate_pairs, (("MAT-A", "MAT-B"),))
        return audit_dimension_candidates(records, report, schema_version=schema_version)

    def test_inverted_dimensions_expose_real_legacy_candidate(self) -> None:
        result = self._audit(
            "PARAFUSO 1/2 X 2 POL CLASSE 8", "PARAFUSO 2 X 1/2 POL CLASSE 8"
        )
        self.assertEqual(result["total_legacy_candidate_pairs"], 1)
        self.assertEqual(result["relations"]["MISMATCH"], 1)
        self.assertNotIn("legacy_candidate_origin", result["pairs"][0])
        self.assertEqual(result["pairs"][0]["material_ids"], ["MAT-A", "MAT-B"])
        self.assertTrue(result["pairs"][0]["lexical_conflict_requires_review"])
        self.assertFalse(result["candidate_selection_changed"])
        self.assertFalse(result["physical_identity_verified"])
        self.assertEqual(result["human_review"], "NOT_RECORDED")

    def test_equivalent_fraction_does_not_claim_a_conflict(self) -> None:
        result = self._audit(
            "PARAFUSO 1/2 X 2 POL CLASSE 8", "PARAFUSO 0.5 X 2 POLEGADAS CLASSE 8"
        )
        self.assertEqual(result["relations"]["MATCH"], 1)
        self.assertFalse(result["pairs"][0]["lexical_conflict_requires_review"])
        self.assertFalse(result["physical_identity_verified"])

    def test_cross_unit_remains_unknown(self) -> None:
        result = self._audit(
            "PARAFUSO 10 X 30 MM CLASSE 8", "PARAFUSO 10 X 30 IN CLASSE 8"
        )
        self.assertEqual(result["relations"]["UNKNOWN"], 1)
        self.assertFalse(result["pairs"][0]["lexical_conflict_requires_review"])

    def test_exact_part_and_manufacturer_origin_is_visible_even_with_dimensional_conflict(self) -> None:
        first = MaterialRecord(
            material_id="MAT-A", description_short="PARAFUSO 1/2 X 2 POL CLASSE 8",
            unit="PC", material_group="FIXADORES", status="ACTIVE",
            manufacturer_part_number="P-123", manufacturer="FABRICANTE A",
        )
        second = MaterialRecord(
            material_id="MAT-B", description_short="PARAFUSO 2 X 1/2 POL CLASSE 8",
            unit="PC", material_group="FIXADORES", status="ACTIVE",
            manufacturer_part_number="P-123", manufacturer="FABRICANTE A",
        )
        records = (first, second)
        report = diagnose_catalog_quality(records, catalog_id="SYN-PN")
        self.assertEqual(report.duplicate_pairs, (("MAT-A", "MAT-B"),))
        result = audit_dimension_candidates(records, report, schema_version="v2")
        self.assertEqual(result["pairs"][0]["legacy_candidate_origin"], "EXACT_PART_MANUFACTURER")
        self.assertEqual(result["relations"]["MISMATCH"], 1)
        self.assertFalse(result["candidate_selection_changed"])
        self.assertEqual(result["human_review"], "NOT_RECORDED")

    def test_partial_part_match_still_uses_description_heuristic(self) -> None:
        first = MaterialRecord(
            material_id="MAT-A", description_short="PARAFUSO 1/2 X 2 POL CLASSE 8",
            unit="PC", material_group="FIXADORES", status="ACTIVE",
            manufacturer_part_number="P-123", manufacturer="FABRICANTE A",
        )
        second = MaterialRecord(
            material_id="MAT-B", description_short="PARAFUSO 2 X 1/2 POL CLASSE 8",
            unit="PC", material_group="FIXADORES", status="ACTIVE",
            manufacturer_part_number="P-123", manufacturer="FABRICANTE B",
        )
        records = (first, second)
        report = diagnose_catalog_quality(records, catalog_id="SYN-MAKER")
        self.assertEqual(report.duplicate_pairs, (("MAT-A", "MAT-B"),))
        result = audit_dimension_candidates(records, report, schema_version="v2")
        self.assertEqual(result["pairs"][0]["legacy_candidate_origin"], "DESCRIPTION_HEURISTIC")
        self.assertEqual(result["relations"]["MISMATCH"], 1)

    def test_json_contract_preserves_v1_shape_and_origin_enumeration(self) -> None:
        """Legacy strict readers keep exact keys; v2 is explicitly requested."""
        descriptions = ("PARAFUSO 1/2 X 2 POL CLASSE 8",
                        "PARAFUSO 2 X 1/2 POL CLASSE 8")
        legacy = self._audit(*descriptions)
        result = self._audit(*descriptions, schema_version="v2")
        self.assertEqual(legacy["schema_version"], "agent_lab.dimension_candidate_audit.v1")
        self.assertEqual(result["schema_version"], "agent_lab.dimension_candidate_audit.v2")
        self.assertEqual(set(legacy["pairs"][0]), {
            "material_ids", "dimension_relation", "lexical_conflict_requires_review",
        })
        projected = json.loads(json.dumps(result))
        projected["schema_version"] = legacy["schema_version"]
        for finding in projected["pairs"]:
            del finding["legacy_candidate_origin"]
        self.assertEqual(projected, legacy)
        self.assertEqual(
            set(result),
            {
                "schema_version", "catalog_id", "total_legacy_candidate_pairs",
                "relations", "pairs", "candidate_selection_changed",
                "physical_identity_verified", "human_review", "interpretation",
            },
        )
        pair = result["pairs"][0]
        self.assertEqual(
            set(pair),
            {
                "material_ids", "dimension_relation",
                "legacy_candidate_origin", "lexical_conflict_requires_review",
            },
        )
        self.assertIn(
            pair["legacy_candidate_origin"],
            {"EXACT_PART_MANUFACTURER", "DESCRIPTION_HEURISTIC"},
        )
        self.assertEqual(sum(result["relations"].values()), result["total_legacy_candidate_pairs"])
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_repeated_audit_remains_deterministic_and_read_only(self) -> None:
        records = (
            _material("MAT-A", "PARAFUSO 1/2 X 2 POL CLASSE 8"),
            _material("MAT-B", "PARAFUSO 2 X 1/2 POL CLASSE 8"),
        )
        report = diagnose_catalog_quality(records, catalog_id="DIM-STABILITY")
        before_pairs = report.duplicate_pairs
        first = audit_dimension_candidates(records, report)
        second = audit_dimension_candidates(records, report)
        self.assertEqual(first, second)
        self.assertEqual(report.duplicate_pairs, before_pairs)
        self.assertFalse(first["candidate_selection_changed"])
        self.assertFalse(first["physical_identity_verified"])

    def test_unsupported_schema_version_is_rejected(self) -> None:
        records = (_material("MAT-A", "PARAFUSO 1/2 X 2 POL"),)
        report = diagnose_catalog_quality(records, catalog_id="CAT")
        with self.assertRaises(ValueError):
            audit_dimension_candidates(records, report, schema_version="v3")

    def test_different_catalog_is_rejected(self) -> None:
        records = (_material("MAT-A", "PARAFUSO 1/2 X 2 POL"),)
        report = diagnose_catalog_quality(records, catalog_id="CAT")
        with self.assertRaises(ValueError):
            audit_dimension_candidates((_material("MAT-B", "PARAFUSO 1/2 X 2 POL"),), report)

    def test_real_csv_cli_path_produces_machine_readable_audit(self) -> None:
        text = (
            "material_id,description_short,unit,material_group,status\n"
            "MAT-A,PARAFUSO 1/2 X 2 POL CLASSE 8,PC,FIXADORES,ACTIVE\n"
            "MAT-B,PARAFUSO 2 X 1/2 POL CLASSE 8,PC,FIXADORES,ACTIVE\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "synthetic.csv"
            file.write_text(text, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([str(file), "--catalog-id", "SYN-CLI"])
            v2_output = io.StringIO()
            with contextlib.redirect_stdout(v2_output):
                self.assertEqual(main([str(file), "--catalog-id", "SYN-CLI",
                                       "--schema-version", "v2"]), 0)
        self.assertEqual(result, 0)
        v2 = json.loads(v2_output.getvalue())
        self.assertEqual(v2["schema_version"], "agent_lab.dimension_candidate_audit.v2")
        self.assertEqual(v2["pairs"][0]["legacy_candidate_origin"], "DESCRIPTION_HEURISTIC")
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["schema_version"], "agent_lab.dimension_candidate_audit.v1")
        self.assertNotIn("legacy_candidate_origin", payload["pairs"][0])
        self.assertEqual(payload["catalog_id"], "SYN-CLI")
        self.assertEqual(payload["total_legacy_candidate_pairs"], 1)
        self.assertEqual(payload["relations"]["MISMATCH"], 1)


if __name__ == "__main__":
    unittest.main()
