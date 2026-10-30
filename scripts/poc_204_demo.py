"""Reproducible, synthetic-only physical artifact demo for Issue #204.

Run: python scripts/poc_204_demo.py --output-dir /tmp/poc-204-demo
"""
import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "poc_204_catalog_synthetic_v1.csv"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output_dir
    if output.exists():
        raise FileExistsError("refusing to replace a previous demonstration")
    fixture_data = FIXTURE.read_bytes()
    output.mkdir(parents=True)
    reports = []
    manifest_data = []
    triage_data = []
    for ordinal in (1, 2):
        directory = output / f"run-{ordinal}"
        directory.mkdir()
        target = directory / "report.json"
        cmd = [
            sys.executable, "-m", "agent_lab.poc_audit_cli",
            str(FIXTURE), str(target), "--catalog-id", "POC-204-SYNTHETIC",
        ]
        subprocess.run(cmd, check=True, cwd=ROOT)
        # Independent fail-closed consumer: never trust a partial/mixed pair.
        verified = subprocess.run(
            [sys.executable, "-m", "agent_lab.poc_audit_verify", str(target)],
            check=True, cwd=ROOT, capture_output=True, text=True,
        )
        if json.loads(verified.stdout)["status"] != "REPORT_AND_MANIFEST_VALIDATED":
            raise ValueError("independent verifier did not accept report/manifest pair")
        content = target.read_bytes()
        manifest = (directory / "report.json.manifest.json").read_bytes()
        parsed_manifest = json.loads(manifest)
        if parsed_manifest["report_sha256"] != sha256(content):
            raise ValueError("manifest failed byte-level SHA-256 verification")
        payload = json.loads(content)
        if payload["summary"]["total_records"] != 3:
            raise ValueError("unexpected catalog cardinality")
        if payload["catalog"]["source_sha256"] is not None or payload["catalog"]["provenance_status"] != "UNAVAILABLE":
            raise ValueError("source custody was asserted without proof")
        if any(r["source_row"] is not None or r["human_review"]["status"] != "NOT_RECORDED" for r in payload["records"]):
            raise ValueError("unverified physical row or fabricated human review")
        # Read-only, fail-closed triage consumes the validated *published pair*.
        # Export contains automated recommendations, never a HumanReview event.
        triage = subprocess.run(
            [sys.executable, "-m", "agent_lab.poc_audit_triage", str(target)],
            check=True, cwd=ROOT, capture_output=True,
        ).stdout
        triage_rows = list(csv.DictReader(io.StringIO(triage.decode("utf-8"))))
        if len(triage_rows) != 3:
            raise ValueError("triage view lost catalog records")
        if any(
            row["human_review_status"] != "NOT_RECORDED"
            or row["source_row_status"] != "UNAVAILABLE"
            or row["source_custody_status"] != "UNAVAILABLE"
            for row in triage_rows
        ):
            raise ValueError("triage invented human review or source custody")
        (directory / "triage.csv").write_bytes(triage)
        triage_data.append(triage)
        reports.append(content)
        manifest_data.append(manifest)

    if (reports[0] != reports[1] or manifest_data[0] != manifest_data[1]
            or triage_data[0] != triage_data[1]):
        raise ValueError("non-deterministic replay, manifest or triage")
    evidence = {
        "schema_version": "poc_204_demo_evidence.v1",
        "scope": "synthetic CSV structural demonstration only; no HITL-E2E, GT or scale claim",
        "input_fixture": FIXTURE.relative_to(ROOT).as_posix(),
        "input_sha256_observed_by_runner": sha256(fixture_data),
        "input_custody_scope": "bytes observed in the demo checkout; not exporter-verified original source custody",
        "report_sha256_run_1": sha256(reports[0]),
        "report_sha256_run_2": sha256(reports[1]),
        "replay_byte_identical": True,
        "manifest_byte_identical": True,
        "triage_sha256_run_1": sha256(triage_data[0]),
        "triage_sha256_run_2": sha256(triage_data[1]),
        "triage_byte_identical": True,
        "triage_record_count": 3,
        "triage_scope": "read-only automated recommendations; not human review",
        "human_review": "NOT_RECORDED",
        "source_row": "UNAVAILABLE",
        "source_sha256_in_export": "UNAVAILABLE",
        "report_count": 2,
        "material_count": 3,
        "two_file_crash_atomicity": "NOT_GUARANTEED; verify paired manifest before consumption",
    }
    evidence_bytes = (json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    (output / "evidence.json").write_bytes(evidence_bytes)
    print(json.dumps(evidence, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
