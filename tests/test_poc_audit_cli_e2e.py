"""Physical CSV -> CLI -> report/manifest regression for PoC Issue #204.

This suite does not claim industrial accuracy or verified source-row custody.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_lab.poc_audit_report import write_poc_audit_report
from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import GovernanceAssessment, GovernanceDecision

FIXTURE = Path(__file__).parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"


def run_cli(source, target, catalog_id="POC-204-SYNTHETIC"):
    return subprocess.run(
        [
            sys.executable, "-m", "agent_lab.poc_audit_cli",
            str(source), str(target), "--catalog-id", catalog_id,
        ],
        capture_output=True, text=True, check=False,
    )


class PocAuditPhysicalE2ETests(unittest.TestCase):
    def test_two_real_cli_invocations_replay_identical_bytes_and_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root / "first.json", root / "second.json"
            one, two = run_cli(FIXTURE, a), run_cli(FIXTURE, b)
            self.assertEqual(one.returncode, 0, one.stderr)
            self.assertEqual(two.returncode, 0, two.stderr)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(
                (root / "first.json.manifest.json").read_bytes(),
                (root / "second.json.manifest.json").read_bytes(),
            )
            data = a.read_bytes()
            manifest = json.loads((root / "first.json.manifest.json").read_bytes())
            self.assertEqual(manifest["report_sha256"], hashlib.sha256(data).hexdigest())
            report = json.loads(data)
            self.assertEqual(report["summary"]["total_records"], 3)
            self.assertEqual(
                [x["material_id"] for x in report["records"]],
                ["M-SYN-001", "M-SYN-002", "M-SYN-003"],
            )
            self.assertEqual(report["catalog"]["source_sha256"], None)
            self.assertEqual(report["catalog"]["provenance_status"], "UNAVAILABLE")
            self.assertEqual(report["engine"]["execution_trace_status"], "UNAVAILABLE")
            for record in report["records"]:
                self.assertIsNone(record["source_row"])
                self.assertEqual(record["source_row_status"], "UNAVAILABLE")
                self.assertEqual(record["human_review"]["status"], "NOT_RECORDED")
                self.assertIsNone(record["human_review"]["decision"])

    def test_invalid_header_leaves_no_report_or_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "bad.csv"
            bad.write_text("material_id,unexpected\nM-001,NO\n", encoding="utf-8")
            target = root / "output.json"
            result = run_cli(bad, target)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())
            self.assertFalse((root / "output.json.manifest.json").exists())

    def test_duplicate_catalog_identities_fail_before_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "duplicate.csv"
            bad.write_text("material_id,description_short\nM-001,X\nM-001,Y\n", encoding="utf-8")
            target = root / "output.json"
            self.assertNotEqual(run_cli(bad, target).returncode, 0)
            self.assertFalse(target.exists())

    def test_malformed_multiline_csv_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "malformed.csv"
            bad.write_text('material_id,description_short\nM-001,"missing quote\n', encoding="utf-8")
            target = root / "output.json"
            self.assertNotEqual(run_cli(bad, target).returncode, 0)
            self.assertFalse(target.exists())

    def test_publication_failure_rolls_back_report_and_manifest(self):
        a = GovernanceAssessment(
            material_id="Z", completeness=0.5, confidence=0.8,
            decision=GovernanceDecision.REVIEW,
        )
        report = CatalogQualityReport(catalog_id="TEST", assessments=(a,))
        real_link = os.link
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "out.json"

            def fail_second_link(source, destination):
                if str(destination).endswith(".manifest.json"):
                    raise OSError("simulated manifest publish failure")
                return real_link(source, destination)

            with patch("agent_lab.poc_audit_report.os.link", side_effect=fail_second_link):
                with self.assertRaisesRegex(OSError, "simulated"):
                    write_poc_audit_report(report, target)
            self.assertFalse(target.exists())
            self.assertFalse((root / "out.json.manifest.json").exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_existing_manifest_prevents_report_and_preserves_existing_bytes(self):
        report = CatalogQualityReport(catalog_id="EMPTY", assessments=())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "out.json"
            manifest = root / "out.json.manifest.json"
            manifest.write_bytes(b"existing-evidence")
            with self.assertRaises(FileExistsError):
                write_poc_audit_report(report, target)
            self.assertEqual(manifest.read_bytes(), b"existing-evidence")
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
