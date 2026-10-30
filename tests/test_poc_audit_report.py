"""Contract tests for structural report MVP (#204)."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import GovernanceAssessment, GovernanceDecision
from agent_lab.poc_audit_report import (
    build_report_manifest, canonical_report_bytes, project_poc_audit_report,
    validate_poc_audit_report, write_poc_audit_report,
)


def sample():
    a = GovernanceAssessment(material_id="B", completeness=0.5, confidence=0.8, decision=GovernanceDecision.REVIEW)
    return CatalogQualityReport(catalog_id="SYNTHETIC", assessments=(a,))


class PocAuditReportTests(unittest.TestCase):
    def test_project_structural_report(self):
        p = project_poc_audit_report(sample())
        self.assertEqual(p["schema_version"], "poc_audit_report.v0")
        self.assertEqual(p["summary"]["total_records"], 1)
        self.assertEqual(p["records"][0]["recommendation"], "REVIEW")
        self.assertEqual(p["records"][0]["human_review"]["status"], "NOT_RECORDED")
        self.assertIsNone(p["records"][0]["source_row"])
        self.assertIsNone(p["catalog"]["source_sha256"])

    def test_empty_catalog_ratios_are_null(self):
        p = project_poc_audit_report(CatalogQualityReport(catalog_id="EMPTY", assessments=()))
        self.assertIsNone(p["summary"]["average_completeness"])
        self.assertIsNone(p["summary"]["clean_records_ratio"])

    def test_replay_is_byte_identical(self):
        p = project_poc_audit_report(sample())
        self.assertEqual(canonical_report_bytes(p), canonical_report_bytes(project_poc_audit_report(sample())))

    def test_manifest_digest_is_of_exact_report_bytes(self):
        data = canonical_report_bytes(project_poc_audit_report(sample()))
        self.assertEqual(build_report_manifest(data)["report_sha256"], hashlib.sha256(data).hexdigest())

    def test_unknown_version_rejected(self):
        p = project_poc_audit_report(sample())
        p["schema_version"] = "future"
        with self.assertRaises(ValueError):
            validate_poc_audit_report(p)

    def test_provenance_forgery_rejected(self):
        p = project_poc_audit_report(sample())
        p["records"][0]["source_row"] = 2
        with self.assertRaises(ValueError):
            canonical_report_bytes(p)

    def test_human_decision_forgery_rejected(self):
        p = project_poc_audit_report(sample())
        p["records"][0]["human_review"]["status"] = "RECORDED"
        with self.assertRaises(ValueError):
            canonical_report_bytes(p)

    def test_counter_mismatch_rejected(self):
        p = project_poc_audit_report(sample())
        p["summary"]["total_records"] = 99
        with self.assertRaises(ValueError):
            canonical_report_bytes(p)

    def test_orphan_candidate_rejected(self):
        p = project_poc_audit_report(sample())
        p["records"][0]["duplicate_candidates"] = ["MISSING"]
        with self.assertRaises(ValueError):
            canonical_report_bytes(p)

    def test_write_files_and_protect_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "report.json"
            report_file, manifest_file = write_poc_audit_report(sample(), out)
            data = report_file.read_bytes()
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["report_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(json.loads(data)["summary"]["total_records"], 1)
            with self.assertRaises(FileExistsError):
                write_poc_audit_report(sample(), out)


if __name__ == "__main__":
    unittest.main()
