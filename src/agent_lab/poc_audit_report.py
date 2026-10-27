"""Deterministic structural PoC report; no human action is inferred."""
import hashlib
import json
from pathlib import Path

from .catalog_quality import CatalogQualityReport

SCHEMA_VERSION = "poc_audit_report.v0"
SUMMARY_FIELDS = (
    "total_records", "clean_records_count", "records_with_blocking_issues_count",
    "records_with_non_blocking_issues_count", "duplicate_candidate_records_count",
    "total_issues_count", "duplicate_pairs_count", "clean_records_ratio",
    "average_completeness",
)


def project_poc_audit_report(report: CatalogQualityReport) -> dict:
    """Pure projection from the validated domain read-model, conservatively scoped."""
    if not isinstance(report, CatalogQualityReport):
        raise TypeError("report must be CatalogQualityReport")
    ids = [a.material_id for a in report.assessments]
    if ids != sorted(set(ids)):
        raise ValueError("noncanonical assessment identities")
    records = []
    for a in report.assessments:
        records.append({
            "material_id": a.material_id,
            "recommendation": a.decision.value,
            "completeness": a.completeness,
            "confidence": a.confidence,
            "normalized_description": a.normalized_description,
            "suggested_group": a.suggested_group,
            "issues": [
                {
                    "issue_type": issue.issue_type.value,
                    "field_name": issue.field_name,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in a.issues
            ],
            "duplicate_candidates": list(a.duplicate_candidates),
            "evidence": list(a.evidence),
            "evidence_projection_status": "NOT_DEFINED",
            "source_row": None,
            "source_row_status": "UNAVAILABLE",
            "human_review": {
                "status": "NOT_RECORDED",
                "decision": None,
                "actor_ref": None,
                "event_ref": None,
            },
        })
    payload = {
        "schema_version": SCHEMA_VERSION,
        "catalog": {
            "catalog_id": report.catalog_id,
            "source_kind": "UNKNOWN",
            "source_ref": None,
            "source_sha256": None,
            "provenance_status": "UNAVAILABLE",
        },
        "engine": {"source_commit": None, "execution_trace_status": "UNAVAILABLE"},
        "summary": {field: getattr(report, field) for field in SUMMARY_FIELDS},
        "records": records,
        "duplicate_pairs": [list(pair) for pair in report.duplicate_pairs],
        "limitations": [
            "Synthetic structural demonstration only; candidate pairs are not verified duplicates.",
            "No independent semantic precision/recall or 100k-SKU performance claim.",
            "No human review event, source-line map, or verified original-byte custody supplied.",
        ],
    }
    validate_poc_audit_report(payload)
    return payload


def validate_poc_audit_report(payload: dict) -> None:
    """Reject schema drift, invented provenance, orphan pairs and inconsistent counts."""
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "catalog", "engine", "summary", "records",
        "duplicate_pairs", "limitations"
    }:
        raise ValueError("unexpected report envelope")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    catalog = payload["catalog"]
    if not isinstance(catalog, dict) or set(catalog) != {
        "catalog_id", "source_kind", "source_ref", "source_sha256", "provenance_status"
    }:
        raise ValueError("invalid catalog metadata")
    if not isinstance(catalog["catalog_id"], str) or not catalog["catalog_id"].strip():
        raise ValueError("invalid catalog identity")
    if catalog["source_kind"] != "UNKNOWN" or catalog["source_ref"] is not None or catalog["source_sha256"] is not None or catalog["provenance_status"] != "UNAVAILABLE":
        raise ValueError("unverified source provenance")
    if payload["engine"] != {"source_commit": None, "execution_trace_status": "UNAVAILABLE"}:
        raise ValueError("unverified execution metadata")
    records = payload["records"]
    if not isinstance(records, list):
        raise ValueError("records must be list")
    ids = [r["material_id"] for r in records]
    if ids != sorted(set(ids)) or any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in ids):
        raise ValueError("invalid record identity or ordering")
    all_pairs = set()
    for r in records:
        if set(r) != {"material_id", "recommendation", "completeness", "confidence", "normalized_description", "suggested_group", "issues", "duplicate_candidates", "evidence", "evidence_projection_status", "source_row", "source_row_status", "human_review"}:
            raise ValueError("unexpected record schema")
        if r["recommendation"] not in ("APPROVE", "REVIEW", "REJECT"):
            raise ValueError("invalid recommendation")
        if any(type(r[k]) not in (int, float) or not 0 <= r[k] <= 1 for k in ("confidence", "completeness")):
            raise ValueError("invalid scores")
        if r["source_row"] is not None or r["source_row_status"] != "UNAVAILABLE":
            raise ValueError("unverified physical row")
        if r["human_review"] != {"status": "NOT_RECORDED", "decision": None, "actor_ref": None, "event_ref": None}:
            raise ValueError("unverified human review")
        if r["evidence_projection_status"] != "NOT_DEFINED":
            raise ValueError("unsupported evidence projection")
        candidates = r["duplicate_candidates"]
        if not isinstance(candidates, list) or candidates != sorted(set(candidates)) or any(x == r["material_id"] or x not in ids for x in candidates):
            raise ValueError("invalid candidate list")
        if not isinstance(r["evidence"], list) or any(not isinstance(x, str) for x in r["evidence"]):
            raise ValueError("invalid evidence")
        if not isinstance(r["issues"], list):
            raise ValueError("invalid issues")
        for issue in r["issues"]:
            if not isinstance(issue, dict) or set(issue) != {"issue_type", "field_name", "message", "severity"} or issue["severity"] not in ("INFO", "WARNING", "BLOCKING"):
                raise ValueError("invalid issue representation")
        for other in candidates:
            all_pairs.add(tuple(sorted((r["material_id"], other))))
    for r in records:
        for other in r["duplicate_candidates"]:
            if r["material_id"] not in records[ids.index(other)]["duplicate_candidates"]:
                raise ValueError("asymmetric duplicate relation")
    pairs = payload["duplicate_pairs"]
    if pairs != [list(p) for p in sorted(all_pairs)]:
        raise ValueError("duplicate pairs disagree with records")
    s = payload["summary"]
    if not isinstance(s, dict) or set(s) != set(SUMMARY_FIELDS):
        raise ValueError("invalid summary schema")
    n = len(records)
    computed = {
        "total_records": n,
        "clean_records_count": sum(not r["issues"] for r in records),
        "records_with_blocking_issues_count": sum(any(i["severity"] == "BLOCKING" for i in r["issues"]) for r in records),
        "records_with_non_blocking_issues_count": sum(bool(r["issues"]) and not any(i["severity"] == "BLOCKING" for i in r["issues"]) for r in records),
        "duplicate_candidate_records_count": sum(bool(r["duplicate_candidates"]) for r in records),
        "total_issues_count": sum(len(r["issues"]) for r in records),
        "duplicate_pairs_count": len(pairs),
        "clean_records_ratio": sum(not r["issues"] for r in records) / n if n else None,
        "average_completeness": sum(r["completeness"] for r in records) / n if n else None,
    }
    if s != computed:
        raise ValueError("summary does not match records")
    if not isinstance(payload["limitations"], list) or not payload["limitations"]:
        raise ValueError("missing limitations")


def canonical_report_bytes(payload: dict) -> bytes:
    validate_poc_audit_report(payload)
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def build_report_manifest(payload_bytes: bytes) -> dict:
    """Digest of the exact canonical report bytes, separate from source-file digest."""
    return {"schema_version": "poc_audit_manifest.v0", "report_sha256": hashlib.sha256(payload_bytes).hexdigest()}


def write_poc_audit_report(report: CatalogQualityReport, output_path: str | Path) -> tuple[Path, Path]:
    """Write validated report and separate manifest; never overwrite existing artifacts."""
    payload = project_poc_audit_report(report)
    encoded = canonical_report_bytes(payload)
    out = Path(output_path)
    manifest = out.with_name(out.name + ".manifest.json")
    if out.exists() or manifest.exists():
        raise FileExistsError("refusing to overwrite report or manifest")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("xb") as f:
        f.write(encoded)
    manifest_bytes = (json.dumps(build_report_manifest(encoded), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with manifest.open("xb") as f:
        f.write(manifest_bytes)
    return out, manifest
