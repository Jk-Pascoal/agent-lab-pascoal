"""Regression tests for the revision-bound acceptance collector (not human acceptance)."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "acceptance_215", Path(__file__).resolve().parents[1] / "scripts" / "acceptance_215.py"
)
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class AcceptanceCollectorTests(unittest.TestCase):
    def invoke(self, output, head="a" * 40, dirty="", expected=None, code=0):
        expected = head if expected is None else expected
        with patch("sys.argv", ["acceptance_215", "--output", str(output),
                               "--expected-head", expected]), \
             patch.object(collector.subprocess, "check_output",
                          side_effect=[head + "\n", dirty]) as check, \
             patch.object(collector.subprocess, "run",
                          return_value=subprocess.CompletedProcess([], code, "stdout", "stderr")) as run, \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                result = collector.main()
            except SystemExit as exc:
                result = exc.code
            return result, check.call_count, run.call_count

    def test_wrong_revision_stops_before_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            self.assertEqual(self.invoke(output, expected="b" * 40), (2, 1, 0))
            self.assertFalse(output.exists())

    def test_dirty_checkout_stops_before_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            self.assertEqual(self.invoke(output, dirty=" M tracked.py\n"), (2, 2, 0))
            self.assertFalse(output.exists())

    def test_failed_suite_preserves_failure_and_no_human_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            self.assertEqual(self.invoke(output, code=1), (1, 2, 1))
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["head"], "a" * 40)
            self.assertEqual(report["automated_exit_code"], 1)
            self.assertEqual(report["automated_log"], "stdoutstderr")
            self.assertEqual(report["human_acceptance"], "NOT_RECORDED")
            self.assertEqual(len(report["manual_cases"]), 9)
            self.assertTrue(all(c["status"] == "NOT_RUN" and c["evidence"] is None
                                for c in report["manual_cases"]))

    def test_success_never_implies_human_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            self.assertEqual(self.invoke(output), (0, 2, 1))
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["human_acceptance"], "NOT_RECORDED")
            self.assertTrue(all(c["status"] == "NOT_RUN" for c in report["manual_cases"]))

    def test_existing_evidence_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            output.write_text("original", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.invoke(output)
            self.assertEqual(output.read_text(encoding="utf-8"), "original")
