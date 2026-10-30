"""Safety contract tests for the cross-chat Agent Lab handoff (#209)."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_session_handoff import (  # noqa: E402
    HandoffContractError, load_handoff, validate_handoff,
)


class SessionHandoffTests(unittest.TestCase):
    def test_current_handoff_is_valid_and_references_real_files(self):
        self.assertTrue(validate_handoff(load_handoff(), ROOT))

    def test_unapproved_production_provenance_is_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["current_product"]["source_original_custody"] = "VERIFIED"
        with self.assertRaisesRegex(HandoffContractError, "source_original_custody"):
            validate_handoff(document, ROOT)

    def test_fabricated_human_review_is_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["current_product"]["actual_human_review"] = "RECORDED"
        with self.assertRaisesRegex(HandoffContractError, "actual_human_review"):
            validate_handoff(document, ROOT)

    def test_ground_truth_mutation_is_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["current_product"]["sr001_t02_ground_truth"] = "UNFROZEN"
        with self.assertRaisesRegex(HandoffContractError, "sr001_t02_ground_truth"):
            validate_handoff(document, ROOT)

    def test_calendar_driven_merge_is_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["next_session"]["prohibited"] = []
        with self.assertRaisesRegex(HandoffContractError, "contribution-only merge"):
            validate_handoff(document, ROOT)

    def test_missing_functional_priority_or_issue_is_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["next_session"]["priority"] = "DOCUMENTATION_ONLY"
        with self.assertRaisesRegex(HandoffContractError, "functional priority"):
            validate_handoff(document, ROOT)
        document = copy.deepcopy(load_handoff())
        document["next_session"]["tracking_issue"] = ""
        with self.assertRaisesRegex(HandoffContractError, "functional Issue"):
            validate_handoff(document, ROOT)

    def test_rewritten_historical_dates_are_rejected(self):
        document = copy.deepcopy(load_handoff())
        document["current_product"]["historical_milestones"]["report_planned_end"] = "2026-11-01"
        with self.assertRaisesRegex(HandoffContractError, "deadlines"):
            validate_handoff(document, ROOT)

    def test_operator_cli_returns_success_for_current_snapshot(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_session_handoff.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("HANDOFF CONTRACT OK", completed.stdout)

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "handoff.json"
            path.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
            with self.assertRaisesRegex(HandoffContractError, "duplicate JSON key"):
                load_handoff(path)


if __name__ == "__main__":
    unittest.main()
