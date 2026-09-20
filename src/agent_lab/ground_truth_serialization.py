from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.domain import IssueType
from agent_lab.ground_truth import (
    DuplicatePairGroundTruth,
    LabelProvenance,
    MaterialRuleGroundTruth,
)
from agent_lab.human_review import VerifiedSpecialistIdentity

SCHEMA_VERSION_V1: int = 1
RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH: str = "MATERIAL_RULE_GROUND_TRUTH"
RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH: str = "DUPLICATE_PAIR_GROUND_TRUTH"

_SPECIALIST_REQUIRED_FIELDS = frozenset(
    {
        "specialist_id",
        "identity_provider",
        "identity_subject",
        "verification_id",
        "verified_at",
    }
)

_DUPLICATE_PAIR_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "record_type",
        "ground_truth_id",
        "evaluation_case_id",
        "material_id_a",
        "material_id_b",
        "is_duplicate",
        "provenance",
        "source_reference",
        "annotator",
        "labeled_at",
        "rationale",
    }
)

_MATERIAL_RULE_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "record_type",
        "ground_truth_id",
        "evaluation_case_id",
        "material_id",
        "expected_issue_types",
        "provenance",
        "source_reference",
        "annotator",
        "labeled_at",
        "rationale",
    }
)


def _format_unknown_keys(keys: set[object]) -> list[str]:
    return sorted(repr(key) for key in keys)


def _require_canonical_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"Field {field_name!r} must be a string, got {type(value).__name__}"
        )
    if not value or value != value.strip():
        raise ValueError(
            f"Field {field_name!r} must be a non-empty canonical string without leading or trailing whitespace"
        )
    return value


def _parse_iso_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"Field {field_name!r} must be an ISO 8601 string, got {type(value).__name__}"
        )
    if not value or value != value.strip():
        raise ValueError(
            f"Timestamp for {field_name!r} must be canonical without outer whitespace: {value!r}"
        )
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 timestamp for {field_name!r}: {value!r}"
        ) from exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(
            f"Timestamp for {field_name!r} must be timezone-aware: {value!r}"
        )
    return dt


def _format_specialist(
    specialist: VerifiedSpecialistIdentity,
) -> dict[str, object]:
    return {
        "specialist_id": specialist.specialist_id,
        "identity_provider": specialist.identity_provider,
        "identity_subject": specialist.identity_subject,
        "verification_id": specialist.verification_id,
        "verified_at": specialist.verified_at.isoformat(),
    }


def _parse_specialist(data: Any) -> VerifiedSpecialistIdentity:
    if not isinstance(data, Mapping) or isinstance(data, (str, bytes)):
        raise ValueError(
            f"Field 'annotator' must be a Mapping, got {type(data).__name__}"
        )

    actual_keys = set(data.keys())
    missing = _SPECIALIST_REQUIRED_FIELDS - actual_keys
    if missing:
        raise ValueError(
            f"Missing required specialist field(s): {sorted(missing)}"
        )

    unknown = actual_keys - _SPECIALIST_REQUIRED_FIELDS
    if unknown:
        raise ValueError(
            f"Unknown specialist field(s) detected: {_format_unknown_keys(unknown)}"
        )

    specialist_id = _require_canonical_non_empty_str(
        data["specialist_id"], "specialist_id"
    )
    identity_provider = _require_canonical_non_empty_str(
        data["identity_provider"], "identity_provider"
    )
    identity_subject = _require_canonical_non_empty_str(
        data["identity_subject"], "identity_subject"
    )
    verification_id = _require_canonical_non_empty_str(
        data["verification_id"], "verification_id"
    )
    verified_at = _parse_iso_datetime(data["verified_at"], "verified_at")

    return VerifiedSpecialistIdentity(
        specialist_id=specialist_id,
        identity_provider=identity_provider,
        identity_subject=identity_subject,
        verification_id=verification_id,
        verified_at=verified_at,
    )


def material_rule_ground_truth_to_record(
    ground_truth: MaterialRuleGroundTruth,
) -> dict[str, object]:
    """Serialize a MaterialRuleGroundTruth domain instance into a canonical record dictionary."""
    if not isinstance(ground_truth, MaterialRuleGroundTruth):
        raise TypeError(
            f"ground_truth must be a MaterialRuleGroundTruth instance, got {type(ground_truth).__name__}"
        )

    expected_issues = [
        item.value
        for item in sorted(
            ground_truth.expected_issue_types, key=lambda item: item.value
        )
    ]

    annotator_record = (
        _format_specialist(ground_truth.annotator)
        if ground_truth.annotator is not None
        else None
    )

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "record_type": RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH,
        "ground_truth_id": ground_truth.ground_truth_id,
        "evaluation_case_id": ground_truth.evaluation_case_id,
        "material_id": ground_truth.material_id,
        "expected_issue_types": expected_issues,
        "provenance": ground_truth.provenance.value,
        "source_reference": ground_truth.source_reference,
        "annotator": annotator_record,
        "labeled_at": ground_truth.labeled_at.isoformat(),
        "rationale": ground_truth.rationale,
    }


def material_rule_ground_truth_from_record(
    record: Mapping[str, object],
) -> MaterialRuleGroundTruth:
    """Deserialize a versioned record mapping into an immutable MaterialRuleGroundTruth."""
    if not isinstance(record, Mapping) or isinstance(record, (str, bytes)):
        raise ValueError(
            f"Record must be a Mapping, got {type(record).__name__}"
        )

    actual_keys = set(record.keys())
    missing = _MATERIAL_RULE_REQUIRED_FIELDS - actual_keys
    if missing:
        raise ValueError(f"Missing required field(s): {sorted(missing)}")

    unknown = actual_keys - _MATERIAL_RULE_REQUIRED_FIELDS
    if unknown:
        raise ValueError(
            f"Unknown field(s) detected: {_format_unknown_keys(unknown)}"
        )

    schema_version = record["schema_version"]
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    record_type = record["record_type"]
    if record_type != RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH:
        raise ValueError(
            f"Expected record_type {RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH!r}, got {record_type!r}"
        )

    ground_truth_id = _require_canonical_non_empty_str(
        record["ground_truth_id"], "ground_truth_id"
    )
    evaluation_case_id = _require_canonical_non_empty_str(
        record["evaluation_case_id"], "evaluation_case_id"
    )
    material_id = _require_canonical_non_empty_str(
        record["material_id"], "material_id"
    )

    raw_issue_types = record["expected_issue_types"]
    if not isinstance(raw_issue_types, list):
        raise ValueError(
            f"Field 'expected_issue_types' must be a list, got {type(raw_issue_types).__name__}"
        )

    parsed_issues: list[IssueType] = []
    seen_values: set[str] = set()
    issue_str_list: list[str] = []

    for idx, item in enumerate(raw_issue_types):
        if not isinstance(item, str) or isinstance(item, bool):
            raise ValueError(
                f"expected_issue_types[{idx}] must be a string, got {type(item).__name__}"
            )
        if item != item.strip():
            raise ValueError(
                f"expected_issue_types[{idx}] has leading/trailing whitespace: {item!r}"
            )
        try:
            issue_enum = IssueType(item)
        except ValueError as exc:
            raise ValueError(
                f"Unknown IssueType in expected_issue_types: {item!r}"
            ) from exc

        if issue_enum == IssueType.POSSIBLE_DUPLICATE:
            raise ValueError(
                "POSSIBLE_DUPLICATE is not permitted in MaterialRuleGroundTruth"
            )

        if item in seen_values:
            raise ValueError(
                f"Duplicate issue_type detected in expected_issue_types: {item!r}"
            )
        seen_values.add(item)
        issue_str_list.append(item)
        parsed_issues.append(issue_enum)

    # Validate strict canonical ordering by IssueType.value
    sorted_issue_str_list = sorted(issue_str_list)
    if issue_str_list != sorted_issue_str_list:
        raise ValueError(
            "expected_issue_types is not in canonical sorted order by IssueType.value"
        )

    raw_provenance = record["provenance"]
    if not isinstance(raw_provenance, str) or isinstance(raw_provenance, bool):
        raise ValueError(
            f"Field 'provenance' must be a string, got {type(raw_provenance).__name__}"
        )
    try:
        provenance = LabelProvenance(raw_provenance)
    except ValueError as exc:
        raise ValueError(
            f"Unknown LabelProvenance: {raw_provenance!r}"
        ) from exc

    raw_annotator = record["annotator"]
    if provenance == LabelProvenance.SYNTHETIC_SPECIFIED:
        if raw_annotator is not None:
            raise ValueError(
                "annotator must be None when provenance is SYNTHETIC_SPECIFIED"
            )
        annotator = None
    elif provenance == LabelProvenance.SPECIALIST_CURATED:
        if raw_annotator is None:
            raise ValueError(
                "annotator is required when provenance is SPECIALIST_CURATED"
            )
        annotator = _parse_specialist(raw_annotator)
    else:
        raise ValueError(f"Unhandled LabelProvenance: {provenance!r}")

    labeled_at = _parse_iso_datetime(record["labeled_at"], "labeled_at")

    if (
        provenance == LabelProvenance.SPECIALIST_CURATED
        and annotator is not None
        and annotator.verified_at > labeled_at
    ):
        raise ValueError("annotator.verified_at cannot be after labeled_at")

    source_reference = _require_canonical_non_empty_str(
        record["source_reference"], "source_reference"
    )
    rationale = _require_canonical_non_empty_str(
        record["rationale"], "rationale"
    )

    return MaterialRuleGroundTruth(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id=material_id,
        expected_issue_types=tuple(parsed_issues),
        provenance=provenance,
        source_reference=source_reference,
        annotator=annotator,
        labeled_at=labeled_at,
        rationale=rationale,
    )


def duplicate_pair_ground_truth_to_record(
    ground_truth: DuplicatePairGroundTruth,
) -> dict[str, object]:
    """Serialize a DuplicatePairGroundTruth domain instance into a canonical record dictionary."""
    if not isinstance(ground_truth, DuplicatePairGroundTruth):
        raise TypeError(
            f"ground_truth must be a DuplicatePairGroundTruth instance, got {type(ground_truth).__name__}"
        )

    annotator_record = (
        _format_specialist(ground_truth.annotator)
        if ground_truth.annotator is not None
        else None
    )

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "record_type": RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH,
        "ground_truth_id": ground_truth.ground_truth_id,
        "evaluation_case_id": ground_truth.evaluation_case_id,
        "material_id_a": ground_truth.material_id_a,
        "material_id_b": ground_truth.material_id_b,
        "is_duplicate": ground_truth.is_duplicate,
        "provenance": ground_truth.provenance.value,
        "source_reference": ground_truth.source_reference,
        "annotator": annotator_record,
        "labeled_at": ground_truth.labeled_at.isoformat(),
        "rationale": ground_truth.rationale,
    }


def duplicate_pair_ground_truth_from_record(
    record: Mapping[str, object],
) -> DuplicatePairGroundTruth:
    """Deserialize a versioned record mapping into an immutable DuplicatePairGroundTruth."""
    if not isinstance(record, Mapping) or isinstance(record, (str, bytes)):
        raise ValueError(
            f"Record must be a Mapping, got {type(record).__name__}"
        )

    actual_keys = set(record.keys())
    missing = _DUPLICATE_PAIR_REQUIRED_FIELDS - actual_keys
    if missing:
        raise ValueError(f"Missing required field(s): {sorted(missing)}")

    unknown = actual_keys - _DUPLICATE_PAIR_REQUIRED_FIELDS
    if unknown:
        raise ValueError(
            f"Unknown field(s) detected: {_format_unknown_keys(unknown)}"
        )

    schema_version = record["schema_version"]
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported or invalid schema_version: {schema_version!r}"
        )

    record_type = record["record_type"]
    if record_type != RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH:
        raise ValueError(
            f"Expected record_type {RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH!r}, got {record_type!r}"
        )

    ground_truth_id = _require_canonical_non_empty_str(
        record["ground_truth_id"], "ground_truth_id"
    )
    evaluation_case_id = _require_canonical_non_empty_str(
        record["evaluation_case_id"], "evaluation_case_id"
    )
    material_id_a = _require_canonical_non_empty_str(
        record["material_id_a"], "material_id_a"
    )
    material_id_b = _require_canonical_non_empty_str(
        record["material_id_b"], "material_id_b"
    )

    if material_id_a == material_id_b:
        raise ValueError(
            "material_id_a and material_id_b must be different"
        )
    if material_id_a > material_id_b:
        raise ValueError(
            "material_id_a must be less than material_id_b"
        )

    raw_is_duplicate = record["is_duplicate"]
    if type(raw_is_duplicate) is not bool:
        raise ValueError(
            f"Field 'is_duplicate' must be a strict bool, got {type(raw_is_duplicate).__name__}"
        )
    is_duplicate = raw_is_duplicate

    raw_provenance = record["provenance"]
    if not isinstance(raw_provenance, str) or isinstance(raw_provenance, bool):
        raise ValueError(
            f"Field 'provenance' must be a string, got {type(raw_provenance).__name__}"
        )
    try:
        provenance = LabelProvenance(raw_provenance)
    except ValueError as exc:
        raise ValueError(
            f"Unknown LabelProvenance: {raw_provenance!r}"
        ) from exc

    raw_annotator = record["annotator"]
    if provenance == LabelProvenance.SYNTHETIC_SPECIFIED:
        if raw_annotator is not None:
            raise ValueError(
                "annotator must be None when provenance is SYNTHETIC_SPECIFIED"
            )
        annotator = None
    elif provenance == LabelProvenance.SPECIALIST_CURATED:
        if raw_annotator is None:
            raise ValueError(
                "annotator is required when provenance is SPECIALIST_CURATED"
            )
        annotator = _parse_specialist(raw_annotator)
    else:
        raise ValueError(f"Unhandled LabelProvenance: {provenance!r}")

    labeled_at = _parse_iso_datetime(record["labeled_at"], "labeled_at")

    if (
        provenance == LabelProvenance.SPECIALIST_CURATED
        and annotator is not None
        and annotator.verified_at > labeled_at
    ):
        raise ValueError("annotator.verified_at cannot be after labeled_at")

    source_reference = _require_canonical_non_empty_str(
        record["source_reference"], "source_reference"
    )
    rationale = _require_canonical_non_empty_str(
        record["rationale"], "rationale"
    )

    return DuplicatePairGroundTruth(
        evaluation_case_id=evaluation_case_id,
        ground_truth_id=ground_truth_id,
        material_id_a=material_id_a,
        material_id_b=material_id_b,
        is_duplicate=is_duplicate,
        provenance=provenance,
        source_reference=source_reference,
        annotator=annotator,
        labeled_at=labeled_at,
        rationale=rationale,
    )
