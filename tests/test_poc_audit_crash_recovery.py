"""Physical SIGKILL publication probes, not simulated Python exceptions.

These are observational Linux/POSIX process-kill tests for R7 of PoC #204.
They do NOT establish power-loss durability, filesystem atomic multi-file
commits, or crash-safe cleanup of temporary staging files.
"""
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_lab.poc_audit_verify import (
    InvalidPocAuditPairError, verify_poc_audit_report_pair,
)

# Run the exact production writer in a separate process. A patched link call
# triggers a real OS SIGKILL around publication, bypassing try/finally.
_CHILD = r'''
import os
import signal
import sys
from agent_lab.catalog_quality import CatalogQualityReport
from agent_lab.domain import GovernanceAssessment, GovernanceDecision
from agent_lab.poc_audit_report import write_poc_audit_report

kill_point = sys.argv[2]
real_link = os.link
link_count = 0

def probe_link(source, destination):
    global link_count
    if kill_point == "before_first" and link_count == 0:
        os.kill(os.getpid(), signal.SIGKILL)
    real_link(source, destination)
    link_count += 1
    if kill_point == "after_first" and link_count == 1:
        os.kill(os.getpid(), signal.SIGKILL)
    if kill_point == "after_second" and link_count == 2:
        os.kill(os.getpid(), signal.SIGKILL)

# Module 'os' is shared: patch only in this disposable child process.
os.link = probe_link
report = CatalogQualityReport(
    catalog_id="CRASH-PROBE-SYNTHETIC",
    assessments=(GovernanceAssessment(
        material_id="M-CRASH-001",
        completeness=0.5, confidence=0.8,
        decision=GovernanceDecision.REVIEW,
    ),),
)
write_poc_audit_report(report, sys.argv[1])
'''


@unittest.skipUnless(os.name == "posix" and hasattr(signal, "SIGKILL"),
                     "physical SIGKILL probe requires POSIX")
class PocAuditPhysicalCrashTests(unittest.TestCase):
    def test_real_process_kill_at_each_link_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            for point, expected_complete in (
                ("before_first", False),
                ("after_first", False),
                ("after_second", True),
            ):
                with self.subTest(point=point):
                    target = Path(root) / point / "report.json"
                    target.parent.mkdir()
                    manifest = target.with_name("report.json.manifest.json")
                    child = subprocess.run(
                        [sys.executable, "-c", _CHILD, str(target), point],
                        capture_output=True, text=True, check=False,
                        timeout=20,
                    )
                    self.assertEqual(child.returncode, -signal.SIGKILL,
                                     child.stderr)
                    self.assertEqual(target.exists(), point != "before_first")
                    self.assertEqual(manifest.exists(), expected_complete)
                    if expected_complete:
                        verified = verify_poc_audit_report_pair(target)
                        self.assertEqual(
                            verified["catalog"]["provenance_status"],
                            "UNAVAILABLE",
                        )
                        self.assertEqual(
                            verified["records"][0]["human_review"]["status"],
                            "NOT_RECORDED",
                        )
                    else:
                        with self.assertRaises(InvalidPocAuditPairError):
                            verify_poc_audit_report_pair(target)
                        checked = subprocess.run(
                            [sys.executable, "-m", "agent_lab.poc_audit_verify",
                             str(target)],
                            capture_output=True, text=True, check=False,
                        )
                        self.assertNotEqual(checked.returncode, 0)
                        self.assertEqual(checked.stdout, "")

    def test_crashed_partial_pair_is_not_overwritten_by_retry(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "report.json"
            killed = subprocess.run(
                [sys.executable, "-c", _CHILD, str(target), "after_first"],
                capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertEqual(killed.returncode, -signal.SIGKILL)
            existing_bytes = target.read_bytes()
            retry = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_cli",
                 str(Path(__file__).parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"),
                 str(target), "--catalog-id", "CRASH-RETRY"],
                capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(target.read_bytes(), existing_bytes)
            self.assertFalse(target.with_name("report.json.manifest.json").exists())

    def test_new_unique_destination_recovers_without_repairing_old_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            old_target = Path(root) / "crashed.json"
            killed = subprocess.run(
                [sys.executable, "-c", _CHILD, str(old_target), "after_first"],
                capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertEqual(killed.returncode, -signal.SIGKILL)
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(old_target)
            new_target = Path(root) / "new-run.json"
            fresh = subprocess.run(
                [sys.executable, "-m", "agent_lab.poc_audit_cli",
                 str(Path(__file__).parent / "fixtures" / "poc_204_catalog_synthetic_v1.csv"),
                 str(new_target), "--catalog-id", "CRASH-RECOVERY-SYNTHETIC"],
                capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertEqual(
                verify_poc_audit_report_pair(new_target)["summary"]["total_records"],
                3,
            )
            with self.assertRaises(InvalidPocAuditPairError):
                verify_poc_audit_report_pair(old_target)


if __name__ == "__main__":
    unittest.main()
