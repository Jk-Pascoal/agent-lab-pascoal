"""Read-only audit of dimensional evidence behind legacy duplicate candidates.

This does not change candidate selection, scores, frozen experiments or human
review state. It does not establish physical material identity.
"""

import argparse
import json
from collections.abc import Sequence

from .catalog_csv_adapter import load_catalog_materials
from .catalog_quality import CatalogQualityReport, diagnose_catalog_quality
from .dimension_comparison import DimensionPairRelation, compare_ordered_dimensions
from .domain import MaterialRecord
from .normalization import normalize_text


def audit_dimension_candidates(
    records: Sequence[MaterialRecord], report: CatalogQualityReport
) -> dict[str, object]:
    """Explain ordered-dimension evidence for each actual legacy candidate pair.

    UNKNOWN is not equivalent to MATCH. A MISMATCH is evidence to be reviewed,
    not an automatic veto of a possible duplicate.
    """
    by_id = {record.material_id: record for record in records}
    report_ids = {assessment.material_id for assessment in report.assessments}
    if len(by_id) != len(records) or set(by_id) != report_ids:
        raise ValueError("audit catalog and assessment identities do not match")

    findings: list[dict[str, object]] = []
    counts = {relation.value: 0 for relation in DimensionPairRelation}
    for left_id, right_id in report.duplicate_pairs:
        left, right = by_id[left_id], by_id[right_id]
        left_text = f"{left.description_short} {left.long_description}".strip()
        right_text = f"{right.description_short} {right.long_description}".strip()
        relation = compare_ordered_dimensions(left_text, right_text)
        # Mirror the first branch of the legacy selector for traceability.
        # This is explanatory only; it never changes candidate selection.
        left_part = normalize_text(left.manufacturer_part_number)
        right_part = normalize_text(right.manufacturer_part_number)
        left_maker = normalize_text(left.manufacturer)
        right_maker = normalize_text(right.manufacturer)
        candidate_origin = (
            "EXACT_PART_MANUFACTURER"
            if left_part and left_part == right_part
            and left_maker and left_maker == right_maker
            else "DESCRIPTION_HEURISTIC"
        )
        counts[relation.value] += 1
        findings.append(
            {
                "material_ids": [left_id, right_id],
                "dimension_relation": relation.value,
                "legacy_candidate_origin": candidate_origin,
                "lexical_conflict_requires_review": relation is DimensionPairRelation.MISMATCH,
            }
        )

    return {
        "schema_version": "agent_lab.dimension_candidate_audit.v1",
        "catalog_id": report.catalog_id,
        "total_legacy_candidate_pairs": len(report.duplicate_pairs),
        "relations": counts,
        "pairs": findings,
        "candidate_selection_changed": False,
        "physical_identity_verified": False,
        "human_review": "NOT_RECORDED",
        "interpretation": (
            "Read-only lexical evidence; MISMATCH flags review, UNKNOWN cannot "
            "be treated as MATCH, and MATCH does not establish material identity."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", help="CSV synthetic/authorized with canonical columns")
    parser.add_argument("--catalog-id", required=True)
    args = parser.parse_args(argv)
    records = load_catalog_materials(args.input_csv)
    report = diagnose_catalog_quality(records, catalog_id=args.catalog_id)
    audit = audit_dimension_candidates(records, report)
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
