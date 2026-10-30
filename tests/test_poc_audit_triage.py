"""Executable gates for the read-only, verified synthetic triage CSV (#204)."""
import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import GovernanceAssessment, GovernanceDecision
from agent_lab.poc_audit_report import write_poc_audit_report
from agent_lab.poc_audit_triage import FIELDS, verified_triage_csv
from agent_lab.poc_audit_verify import InvalidPocAuditPairError


def make_pair(root):
    report = CatalogQualityReport(
        catalog_id="=UNTRUSTED-CATALOG",
        assessments=(
            GovernanceAssessment(
                material_id="=UNTRUSTED-ID", completeness=1.0, confidence=0.9,
                decision=GovernanceDecision.APPROVE,
            ),
            GovernanceAssessment(
                material_id="M-002", completeness=0.5, confidence=0.8,
                decision=GovernanceDecision.REVIEW,
            ),
        ),
    )
    output = Path(root) / "report.json"
    write_poc_audit_report(report, output)
    return output, output.with_name(output.name + ".manifest.json")


class PocAuditVerifiedTriageTests(unittest.TestCase):
    def test_verified_projection_exports_both_records_without_forging_review(self):
        with tempfile.TemporaryDirectory() as root:
            report_path, manifest = make_pair(root)
            report_before, manifest_before = report_path.read_bytes(), manifest.read_bytes()
            rendered = verified_triage_csv(report_path)
            self.assertEqual(rendered, verified_triage_csv(report_path))
            rows = list(csv.DictReader(io.StringIO(rendered)))
            self.assertEqual(len(rows), 2)
            self.assertEqual(list(rows[0]), list(FIELDS))
            self.assertEqual([r["recommendation"] for r in rows], ["APPROVE", "REVIEW"])
            self.assertEqual([r["human_review_status"] for r in rows], ["NOT_RECORDED"] * 2)
            self.assertEqual([r["source_row_status"] for r in rows], ["UNAVAILABLE"] * 2)
            self.assertEqual([r["source_custody_status"] for r in rows], ["UNAVAILABLE"] * 2)
            self.assertEqual(rows[0]["catalog_id"], "'=UNTRUSTED-CATALOG")
            self.assertEqual(rows[0]["material_id"], "'=UNTRUSTED-ID")
            self.assertEqual(report_path.read_bytes(), report_before)
            self.assertEqual(manifest.read_bytes(), manifest_before)

    def test_actionable_filter_is_only_automated_recommendation(self):
        with tempfile.TemporaryDirectory() as root:
            report_path, _ = make_pair(root)
            rows = list(csv.DictReader(io.StringIO(
                verified_triage_csv(report_path, actionable_only=True)
            )))
            self.assertEqual([r["material_id"] for r in rows], ["M-002"])
            self.assertEqual(rows[0]["recommendation"], "REVIEW")
            self.assertEqual(rows[0]["human_review_status"], "NOT_RECORDED")

    def test_missing_manifest_refuses_without_partial_output(self):
        with tempfile.TemporaryDirectory() as root:
            report_path, manifest = make_pair(root)
            manifest.unlink()
            with self.assertRaises(InvalidPocAuditPairError):
                verified_triage_csv(report_path)
            result = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_triage", str(report_path)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("REFUSED", result.stderr)

    def test_tampered_report_refuses_even_when_manifest_is_present(self):
        with tempfile.TemporaryDirectory() as root:
            report_path, _ = make_pair(root)
            report_path.write_bytes(report_path.read_bytes() + b" ")
            result = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_triage",
                 str(report_path), "--actionable-only"],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_physical_cli_succeeds_with_deterministic_csv(self):
        with tempfile.TemporaryDirectory() as root:
            report_path, _ = make_pair(root)
            command = [sys.executable, "-m", "agent_lab.poc_audit_triage", str(report_path)]
            first = subprocess.run(command, capture_output=True, text=True)
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(len(list(csv.DictReader(io.StringIO(first.stdout)))), 2)


if __name__ == "__main__":
    unittest.main()
