from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened

SCHEMA_VERSION_V1 = 1
EVENT_TYPE_WORKFLOW_CONCLUDED = "WORKFLOW_CONCLUDED"


def _require_str(mapping: Mapping[str, Any], key: str) -> str:
    if key not in mapping:
        raise ValueError(f"Missing required field '{key}'")
    val = mapping[key]
    if type(val) is not str:
        raise ValueError(
            f"Field '{key}' must be a string, got {type(val).__name__}"
        )
    return val


def _require_optional_str(mapping: Mapping[str, Any], key: str) -> str | None:
    if key not in mapping:
        return None
    val = mapping[key]
    if val is None:
        return None
    if type(val) is not str:
        raise ValueError(
            f"Field '{key}' must be a string or None, got {type(val).__name__}"
        )
    return val


def _parse_evidence_item(item: Any) -> GovernanceEvidence:
    if not isinstance(item, Mapping):
        raise ValueError("Evidence item must be a mapping")

    material_id = _require_str(item, "material_id")
    observation = _require_str(item, "observation")
    source_str = _require_str(item, "source")
    issue_type_str = _require_str(item, "issue_type")
    severity_str = _require_str(item, "severity")

    try:
        source = EvidenceSource(source_str)
    except ValueError as exc:
        raise ValueError(f"Invalid EvidenceSource: '{source_str}'") from exc

    try:
        issue_type = IssueType(issue_type_str)
    except ValueError as exc:
        raise ValueError(f"Invalid IssueType: '{issue_type_str}'") from exc

    try:
        severity = IssueSeverity(severity_str)
    except ValueError as exc:
        raise ValueError(f"Invalid IssueSeverity: '{severity_str}'") from exc

    return GovernanceEvidence(
        material_id=material_id,
        source=source,
        issue_type=issue_type,
        observation=observation,
        severity=severity,
    )


def _parse_recommendation(rec: Any) -> DecisionRecommendation:
    if not isinstance(rec, Mapping):
        raise ValueError("Field 'recommendation' must be a mapping")

    material_id = _require_str(rec, "material_id")
    rationale = _require_str(rec, "rationale")
    decision_str = _require_str(rec, "decision")

    try:
        decision = GovernanceDecision(decision_str)
    except ValueError as exc:
        raise ValueError(
            f"Invalid GovernanceDecision: '{decision_str}'"
        ) from exc

    if "requires_human_decision" not in rec:
        raise ValueError("Missing required field 'requires_human_decision'")
    req_hd = rec["requires_human_decision"]
    if req_hd is not True or type(req_hd) is not bool:
        raise ValueError("Field 'requires_human_decision' must be True")

    if "evidence" not in rec:
        raise ValueError("Missing required field 'evidence'")
    ev_list = rec["evidence"]
    if not isinstance(ev_list, list):
        raise ValueError("Field 'evidence' must be a list")

    evidence_tuple = tuple(_parse_evidence_item(item) for item in ev_list)

    for item in evidence_tuple:
        if item.material_id != material_id:
            raise ValueError(
                "Evidence material_id must match recommendation material_id"
            )

    return DecisionRecommendation(
        material_id=material_id,
        decision=decision,
        evidence=evidence_tuple,
        rationale=rationale,
        requires_human_decision=True,
    )


def _parse_reviewer_identity(data: Any) -> VerifiedSpecialistIdentity:
    if not isinstance(data, Mapping):
        raise ValueError("Field 'reviewer_identity' must be a mapping")

    specialist_id = _require_str(data, "specialist_id")
    identity_provider = _require_str(data, "identity_provider")
    identity_subject = _require_str(data, "identity_subject")
    verification_id = _require_str(data, "verification_id")
    verified_at_str = _require_str(data, "verified_at")

    try:
        verified_at = datetime.fromisoformat(verified_at_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime for 'verified_at': '{verified_at_str}'"
        ) from exc

    if verified_at.tzinfo is None or verified_at.utcoffset() is None:
        raise ValueError(
            f"verified_at must be timezone-aware: '{verified_at_str}'"
        )

    return VerifiedSpecialistIdentity(
        specialist_id=specialist_id,
        identity_provider=identity_provider,
        identity_subject=identity_subject,
        verification_id=verification_id,
        verified_at=verified_at,
    )


def _parse_correction_request(data: Any) -> CorrectionRequest:
    if not isinstance(data, Mapping):
        raise ValueError("Correction item must be a mapping")

    field_name = _require_str(data, "field_name")
    reason = _require_str(data, "reason")
    suggested_value = _require_optional_str(data, "suggested_value")

    return CorrectionRequest(
        field_name=field_name,
        reason=reason,
        suggested_value=suggested_value,
    )


def _parse_human_review(data: Any) -> HumanReview:
    if not isinstance(data, Mapping):
        raise ValueError("Field 'review' must be a mapping")

    review_id = _require_str(data, "review_id")
    material_id = _require_str(data, "material_id")
    system_rec_str = _require_str(data, "system_recommendation")
    human_dec_str = _require_str(data, "human_decision")

    try:
        system_recommendation = GovernanceDecision(system_rec_str)
    except ValueError as exc:
        raise ValueError(
            f"Invalid GovernanceDecision: '{system_rec_str}'"
        ) from exc

    try:
        human_decision = HumanDecision(human_dec_str)
    except ValueError as exc:
        raise ValueError(f"Invalid HumanDecision: '{human_dec_str}'") from exc

    if "reviewer_identity" not in data:
        raise ValueError("Missing required field 'reviewer_identity'")
    reviewer_identity = _parse_reviewer_identity(data["reviewer_identity"])

    reviewed_at_str = _require_str(data, "reviewed_at")
    try:
        reviewed_at = datetime.fromisoformat(reviewed_at_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime for 'reviewed_at': '{reviewed_at_str}'"
        ) from exc

    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError(
            f"reviewed_at must be timezone-aware: '{reviewed_at_str}'"
        )

    justification = _require_optional_str(data, "justification")

    corrections_raw = data.get("corrections", [])
    if not isinstance(corrections_raw, list):
        raise ValueError("Field 'corrections' must be a list")

    corrections = tuple(_parse_correction_request(item) for item in corrections_raw)

    return HumanReview(
        review_id=review_id,
        material_id=material_id,
        system_recommendation=system_recommendation,
        human_decision=human_decision,
        reviewer_identity=reviewer_identity,
        reviewed_at=reviewed_at,
        justification=justification,
        corrections=corrections,
    )


def workflow_opened_to_record(event: WorkflowOpened) -> dict[str, object]:
    """Serialize a WorkflowOpened domain event into a versioned dictionary record."""
    if not isinstance(event, WorkflowOpened):
        raise ValueError(
            f"Expected WorkflowOpened instance, got {type(event).__name__}"
        )

    evidence_list: list[dict[str, object]] = [
        {
            "material_id": item.material_id,
            "source": item.source.value,
            "issue_type": item.issue_type.value,
            "observation": item.observation,
            "severity": item.severity.value,
        }
        for item in event.recommendation.evidence
    ]

    rec_dict: dict[str, object] = {
        "material_id": event.recommendation.material_id,
        "decision": event.recommendation.decision.value,
        "rationale": event.recommendation.rationale,
        "requires_human_decision": event.recommendation.requires_human_decision,
        "evidence": evidence_list,
    }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "event_id": event.event_id,
        "workflow_id": event.workflow_id,
        "opened_at": event.opened_at.isoformat(),
        "recommendation": rec_dict,
    }


def workflow_opened_from_record(
    record: Mapping[str, object],
) -> WorkflowOpened:
    """Deserialize a versioned dictionary record into a WorkflowOpened domain event."""
    if not isinstance(record, Mapping):
        raise ValueError(
            f"Expected mapping record, got {type(record).__name__}"
        )

    if "schema_version" not in record:
        raise ValueError("Missing required field 'schema_version'")
    schema_version = record["schema_version"]
    if type(schema_version) is not int or isinstance(schema_version, bool):
        raise ValueError(
            f"schema_version must be an int, got {type(schema_version).__name__}"
        )
    if schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported schema_version: {schema_version}, expected {SCHEMA_VERSION_V1}"
        )

    event_id = _require_str(record, "event_id")
    workflow_id = _require_str(record, "workflow_id")
    opened_at_str = _require_str(record, "opened_at")

    try:
        opened_at = datetime.fromisoformat(opened_at_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime: '{opened_at_str}'"
        ) from exc

    if opened_at.tzinfo is None or opened_at.utcoffset() is None:
        raise ValueError(f"opened_at must be timezone-aware: '{opened_at_str}'")

    if "recommendation" not in record:
        raise ValueError("Missing required field 'recommendation'")
    recommendation = _parse_recommendation(record["recommendation"])

    return WorkflowOpened(
        event_id=event_id,
        workflow_id=workflow_id,
        recommendation=recommendation,
        opened_at=opened_at,
    )


def workflow_concluded_to_record(
    event: WorkflowConcluded,
) -> dict[str, object]:
    """Serialize a WorkflowConcluded domain event into a versioned dictionary record."""
    if not isinstance(event, WorkflowConcluded):
        raise ValueError(
            f"Expected WorkflowConcluded instance, got {type(event).__name__}"
        )

    corrections_list: list[dict[str, object]] = [
        {
            "field_name": item.field_name,
            "reason": item.reason,
            "suggested_value": item.suggested_value,
        }
        for item in event.review.corrections
    ]

    reviewer_identity_dict: dict[str, object] = {
        "specialist_id": event.review.reviewer_identity.specialist_id,
        "identity_provider": event.review.reviewer_identity.identity_provider,
        "identity_subject": event.review.reviewer_identity.identity_subject,
        "verification_id": event.review.reviewer_identity.verification_id,
        "verified_at": event.review.reviewer_identity.verified_at.isoformat(),
    }

    review_dict: dict[str, object] = {
        "review_id": event.review.review_id,
        "material_id": event.review.material_id,
        "system_recommendation": event.review.system_recommendation.value,
        "human_decision": event.review.human_decision.value,
        "reviewer_identity": reviewer_identity_dict,
        "reviewed_at": event.review.reviewed_at.isoformat(),
        "justification": event.review.justification,
        "corrections": corrections_list,
    }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "event_type": EVENT_TYPE_WORKFLOW_CONCLUDED,
        "event_id": event.event_id,
        "workflow_id": event.workflow_id,
        "review": review_dict,
    }


def workflow_concluded_from_record(
    record: Mapping[str, object],
) -> WorkflowConcluded:
    """Deserialize a versioned dictionary record into a WorkflowConcluded domain event."""
    if not isinstance(record, Mapping):
        raise ValueError(
            f"Expected mapping record, got {type(record).__name__}"
        )

    if "schema_version" not in record:
        raise ValueError("Missing required field 'schema_version'")
    schema_version = record["schema_version"]
    if type(schema_version) is not int or isinstance(schema_version, bool):
        raise ValueError(
            f"schema_version must be an int, got {type(schema_version).__name__}"
        )
    if schema_version != SCHEMA_VERSION_V1:
        raise ValueError(
            f"Unsupported schema_version: {schema_version}, expected {SCHEMA_VERSION_V1}"
        )

    event_type = _require_str(record, "event_type")
    if event_type != EVENT_TYPE_WORKFLOW_CONCLUDED:
        raise ValueError(
            f"Unsupported event_type: '{event_type}', expected '{EVENT_TYPE_WORKFLOW_CONCLUDED}'"
        )

    event_id = _require_str(record, "event_id")
    workflow_id = _require_str(record, "workflow_id")

    if "review" not in record:
        raise ValueError("Missing required field 'review'")
    review = _parse_human_review(record["review"])

    return WorkflowConcluded(
        event_id=event_id,
        workflow_id=workflow_id,
        review=review,
    )
