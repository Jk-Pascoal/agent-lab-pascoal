"""Validate the persistent, machine-readable Agent Lab session handoff.

Run: python scripts/verify_session_handoff.py

This is a contract validator, not a claim that the checkpoint is live.
Next sessions must compare its SHA/CI with actual GitHub state.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs" / "operations" / "SESSION_HANDOFF.json"


class HandoffContractError(ValueError):
    """A handoff cannot be used as a trustworthy reentry reference."""


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise HandoffContractError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def load_handoff(path=HANDOFF):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HandoffContractError(f"unreadable handoff: {exc}") from exc


def _ensure(condition, message):
    if not condition:
        raise HandoffContractError(message)


def validate_handoff(doc, root=ROOT):
    """Structural and epistemic invariants; no network or GitHub access."""
    _ensure(type(doc) is dict, "expected JSON object")
    _ensure(doc.get("schema_version") == "agent_lab.session_handoff.v1", "unknown schema_version")

    checkpoint = doc.get("checkpoint")
    _ensure(type(checkpoint) is dict, "missing checkpoint")
    try:
        date.fromisoformat(checkpoint["date"])
    except (TypeError, ValueError, KeyError) as exc:
        raise HandoffContractError("invalid checkpoint date") from exc
    _ensure(checkpoint.get("timezone") == "America/Bahia", "missing local date context")
    _ensure(bool(re.fullmatch(r"[0-9a-f]{40}", str(checkpoint.get("main_sha_at_checkpoint", "")))),
            "unverified main SHA shape")
    _ensure(bool(re.fullmatch(r"[0-9a-f]{40}", str(checkpoint.get("last_functional_merge", "")))),
            "unverified functional merge SHA shape")
    _ensure(type(checkpoint.get("main_tests_passed")) is int and checkpoint["main_tests_passed"] > 0,
            "missing positive baseline count")
    _ensure(checkpoint.get("canonical_runner") == "python -m unittest discover -s tests -v",
            "noncanonical runner")
    _ensure(str(checkpoint.get("main_ci_url", "")).startswith(
        "https://github.com/Jk-Pascoal/agent-lab-pascoal/actions/runs/"), "CI evidence URL missing")

    product = doc.get("current_product")
    _ensure(type(product) is dict, "missing product state")
    invariant_fields = {
        "maturity": "SYNTHETIC_STRUCTURAL_POC_NOT_INDUSTRIAL",
        "source_original_custody": "UNAVAILABLE",
        "physical_source_row": "UNAVAILABLE",
        "actual_human_review": "NOT_RECORDED",
        "two_file_power_loss_atomicity": "NOT_PROVEN",
        "external_independent_pr205_review": "NOT_RECORDED",
        "hitl_end_to_end": "OUT_OF_SCOPE",
        "sr001_t02_ground_truth": "FROZEN_DO_NOT_MUTATE",
        "industrial_100k_sku_readiness": "NOT_PROVEN",
    }
    for field, expected in invariant_fields.items():
        _ensure(product.get(field) == expected, f"invalid unsupported claim: {field}")
    decisions = product.get("decisions")
    _ensure(type(decisions) is dict and decisions.get("D-03") == "PENDING"
            and decisions.get("D-04") == "PENDING", "unapproved schedule decisions")
    milestones = product.get("historical_milestones")
    _ensure(type(milestones) is dict and milestones.get("report_planned_end") == "2026-10-25"
            and milestones.get("poc_target") == "2026-11-20"
            and milestones.get("poc_target_revalidated") is False,
            "original deadlines or unvalidated forecast were rewritten")

    next_session = doc.get("next_session")
    _ensure(type(next_session) is dict, "missing next session")
    _ensure(next_session.get("priority") == "P1_FUNCTIONAL_VERTICAL", "lost functional priority")
    _ensure(next_session.get("tracking_issue")
            == "https://github.com/Jk-Pascoal/agent-lab-pascoal/issues/210",
            "lost next functional Issue")
    _ensure(type(next_session.get("entry_protocol")) is list
            and len(next_session["entry_protocol"]) >= 4, "missing reentry steps")
    _ensure(type(next_session.get("acceptance")) is list
            and len(next_session["acceptance"]) >= 4, "missing acceptance checks")
    _ensure(type(next_session.get("closeout")) is list
            and len(next_session["closeout"]) >= 3, "missing daily closure")
    _ensure("Real source code" in " ".join(next_session["acceptance"]),
            "next session may regress to documentation-only")
    _ensure("Do not merge merely" in " ".join(next_session.get("prohibited", [])),
            "unsafe contribution-only merge allowed")

    sources = doc.get("source_of_truth")
    _ensure(type(sources) is dict, "missing source links")
    required_paths = [
        "AGENTS.md", "docs/PROJECT_COMPASS.md",
        "docs/planning/POC_204_scoped_technical_acceptance_20261030.md",
        "src/agent_lab/poc_audit_cli.py", "src/agent_lab/poc_audit_report.py",
        "src/agent_lab/poc_audit_verify.py", "src/agent_lab/poc_audit_triage.py",
        "scripts/poc_204_demo.py",
        "tests/fixtures/poc_204_catalog_synthetic_v1.csv",
    ]
    provided_paths = set(sources.get("supporting_files", []))
    _ensure(all((root / path).is_file() for path in required_paths),
            "a referenced code/Compass/AGENTS source file is missing")
    _ensure(set(required_paths[-6:]).issubset(provided_paths),
            "supporting files omitted from handoff")
    _ensure((root / "README.md").is_file()
            and "docs/operations/SESSION_HANDOFF.json" in
            (root / "README.md").read_text(encoding="utf-8"),
            "README must point to reentry contract")
    return True


def main():
    try:
        handoff = load_handoff()
        validate_handoff(handoff)
    except HandoffContractError as exc:
        print(f"INVALID HANDOFF: {exc}", file=sys.stderr)
        return 1
    snapshot = handoff["checkpoint"]
    print("HANDOFF CONTRACT OK (snapshot, not live status): "
          f"{snapshot['date']} main={snapshot['main_sha_at_checkpoint'][:12]} "
          f"tests={snapshot['main_tests_passed']}; next issue #210")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
