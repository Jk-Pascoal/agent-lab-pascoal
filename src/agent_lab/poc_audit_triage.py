"""Read-only CSV triage projection of a *verified* PoC #204 report pair.

The verified JSON report remains authoritative. This view is only a synthetic
structural queue of *automated recommendations*, never a HumanReview event.
No CSV is emitted if the report/manifest pair fails independent verification.
"""
import argparse
import csv
import io
import sys
from collections import Counter
from pathlib import Path

from .poc_audit_verify import InvalidPocAuditPairError, verify_poc_audit_report_pair

FIELDS = (
    "catalog_id", "material_id", "recommendation", "completeness",
    "confidence", "blocking_issues", "warning_issues", "info_issues",
    "duplicate_candidate_count", "human_review_status", "source_row_status",
    "source_custody_status",
)


def _spreadsheet_safe(value: str) -> str:
    """Neutralize spreadsheet formula prefixes; JSON retains original IDs."""
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def verified_triage_csv(report_path: str | Path, *, actionable_only: bool = False) -> str:
    """Build all output in memory; never stream partially verified evidence."""
    payload = verify_poc_audit_report_pair(report_path)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for record in payload["records"]:
        if actionable_only and record["recommendation"] not in ("REVIEW", "REJECT"):
            continue
        severities = Counter(item["severity"] for item in record["issues"])
        writer.writerow({
            "catalog_id": _spreadsheet_safe(payload["catalog"]["catalog_id"]),
            "material_id": _spreadsheet_safe(record["material_id"]),
            "recommendation": record["recommendation"],
            "completeness": record["completeness"],
            "confidence": record["confidence"],
            "blocking_issues": severities["BLOCKING"],
            "warning_issues": severities["WARNING"],
            "info_issues": severities["INFO"],
            "duplicate_candidate_count": len(record["duplicate_candidates"]),
            "human_review_status": record["human_review"]["status"],
            "source_row_status": record["source_row_status"],
            "source_custody_status": payload["catalog"]["provenance_status"],
        })
    return output.getvalue()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_json", help="verified report; expects sibling manifest")
    parser.add_argument(
        "--actionable-only", action="store_true",
        help="show automated REVIEW/REJECT recommendations only; NOT human decisions",
    )
    args = parser.parse_args(argv)
    try:
        result = verified_triage_csv(args.report_json, actionable_only=args.actionable_only)
    except (InvalidPocAuditPairError, OSError) as exc:
        parser.exit(1, f"REFUSED: {exc}\n")
    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
