"""Adversarial consumer gates for the synthetic CSV report PoC (#204)."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import GovernanceAssessment, GovernanceDecision
from agent_lab.poc_audit_report import write_poc_audit_report
from agent_lab.poc_audit_verify import (
    InvalidPocAuditPairError, verify_poc_audit_report_pair,
)

FIXTURE = Path(__file__).parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"


def _canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _pair(directory):
    report = CatalogQualityReport(
        catalog_id="CONSUMER-TEST",
        assessments=(GovernanceAssessment(
            material_id="M-001", completeness=0.5, confidence=0.8,
            decision=GovernanceDecision.REVIEW,
        ),),
    )
    target = Path(directory) / "report.json"
    write_poc_audit_report(report, target)
    return target, target.with_name(target.name + ".manifest.json")


def _replace_report_and_rehash(target, manifest_path, report_bytes):
    """Adversarial fixture: valid digest alone must not imply valid schema."""
    target.write_bytes(report_bytes)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    manifest_path.write_bytes(_canonical(manifest))


class PocAuditPairVerifierTests(unittest.TestCase):
    def test_valid_pair_returns_structurally_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target, _ = _pair(directory)
            value = verify_poc_audit_report_pair(target)
            self.assertEqual(value["schema_version"], "poc_audit_report.v0")
            self.assertEqual(value["catalog"]["provenance_status"], "UNAVAILABLE")
            self.assertEqual(value["records"][0]["human_review"]["status"], "NOT_RECORDED")

    def test_missing_manifest_after_partial_publish_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            manifest.unlink()
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(target)

    def test_missing_report_with_orphan_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, _ = _pair(directory)
            target.unlink()
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(target)

    def test_missing_both_files_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(Path(directory) / "never.json")

    def test_corrupted_report_bytes_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, _ = _pair(directory)
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(InvalidPocAuditPairError, "digest"):
                verify_poc_audit_report_pair(target)

    def test_corrupted_manifest_digest_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            obj = json.loads(manifest.read_bytes())
            obj["report_sha256"] = "0" * 64
            manifest.write_bytes(_canonical(obj))
            with self.assertRaisesRegex(InvalidPocAuditPairError, "digest"):
                verify_poc_audit_report_pair(target)

    def test_unknown_manifest_key_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            obj = json.loads(manifest.read_bytes())
            obj["unexpected"] = "unsafe"
            manifest.write_bytes(_canonical(obj))
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(target)

    def test_duplicate_manifest_keys_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest.write_bytes(
                ('{"report_sha256":"' + digest +
                 '","report_sha256":"' + digest +
                 '","schema_version":"poc_audit_manifest.v0"}\n').encode("utf-8")
            )
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(target)

    def test_forged_source_row_is_refused_even_when_digest_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            obj = json.loads(target.read_bytes())
            obj["records"][0]["source_row"] = 42
            _replace_report_and_rehash(target, manifest, _canonical(obj))
            with self.assertRaisesRegex(InvalidPocAuditPairError, "contract"):
                verify_poc_audit_report_pair(target)

    def test_forged_human_review_is_refused_even_when_digest_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            obj = json.loads(target.read_bytes())
            obj["records"][0]["human_review"]["status"] = "RECORDED"
            _replace_report_and_rehash(target, manifest, _canonical(obj))
            with self.assertRaisesRegex(InvalidPocAuditPairError, "contract"):
                verify_poc_audit_report_pair(target)

    def test_noncanonical_report_is_refused_even_when_digest_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            bytes_with_spaces = json.dumps(json.loads(target.read_bytes()), indent=2).encode("utf-8") + b"\n"
            _replace_report_and_rehash(target, manifest, bytes_with_spaces)
            with self.assertRaisesRegex(InvalidPocAuditPairError, "noncanonical"):
                verify_poc_audit_report_pair(target)

    def test_physical_export_then_independent_verifier_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "from-csv.json"
            exported = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_cli",
                 str(FIXTURE), str(target), "--catalog-id", "CONSUMER-CLI-TEST"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(exported.returncode, 0, exported.stderr)
            checked = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_verify", str(target)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            result = json.loads(checked.stdout)
            self.assertEqual(result["status"], "REPORT_AND_MANIFEST_VALIDATED")
            self.assertEqual(result["source_custody"], "UNAVAILABLE")
            self.assertEqual(result["human_review"], "NOT_VERIFIED")
            self.assertEqual(result["report_sha256"], hashlib.sha256(target.read_bytes()).hexdigest())

    def test_verifier_cli_rejects_incomplete_pair_with_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            target, manifest = _pair(directory)
            manifest.unlink()
            result = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_verify", str(target)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("REFUSED", result.stderr)


if __name__ == "__main__":
    unittest.main()
