from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from agent_lab.audit import AuditEvent, AuditEventType
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
)


class ConsistencyIssueType(str, Enum):
    """Categorias discriminadas de inconsistência entre lifecycle e auditoria."""

    MISSING_AUDIT_EVENT = "MISSING_AUDIT_EVENT"
    MISSING_WORKFLOW_CONCLUDED = "MISSING_WORKFLOW_CONCLUDED"
    MATERIAL_ID_MISMATCH = "MATERIAL_ID_MISMATCH"
    ACTOR_ID_MISMATCH = "ACTOR_ID_MISMATCH"
    TIMESTAMP_MISMATCH = "TIMESTAMP_MISMATCH"
    AUDIT_METADATA_MISMATCH = "AUDIT_METADATA_MISMATCH"
    DUPLICATE_REVIEW_ID_IN_LIFECYCLE = "DUPLICATE_REVIEW_ID_IN_LIFECYCLE"
    DUPLICATE_REVIEW_ID_IN_AUDIT = "DUPLICATE_REVIEW_ID_IN_AUDIT"


@dataclass(frozen=True, slots=True)
class ConsistencyIssue:
    """Diagnóstico imutável de uma inconsistência pontual identificada."""

    issue_type: ConsistencyIssueType
    review_id: str
    workflow_id: str | None = None
    audit_event_id: str | None = None
    details: str = ""


@dataclass(frozen=True, slots=True)
class DualWriteConsistencyReport:
    """Relatório estruturado e imutável da verificação de consistência cruzada."""

    total_concluded_events: int
    total_audit_review_events: int
    matched_pairs_count: int
    issues: tuple[ConsistencyIssue, ...] = field(default_factory=tuple)

    @property
    def is_consistent(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)


def verify_dual_write_consistency(
    lifecycle_events: Sequence[WorkflowLifecycleEvent],
    audit_events: Sequence[AuditEvent],
) -> DualWriteConsistencyReport:
    """Verifica a integridade e paridade cruzada entre lifecycle e auditoria."""
    concluded_by_review_id: dict[str, list[WorkflowConcluded]] = defaultdict(list)
    for event in lifecycle_events:
        if isinstance(event, WorkflowConcluded):
            concluded_by_review_id[event.review.review_id].append(event)

    audit_by_review_id: dict[str, list[AuditEvent]] = defaultdict(list)
    for event in audit_events:
        if event.event_type == AuditEventType.HUMAN_REVIEW_RECORDED:
            audit_by_review_id[event.review_id].append(event)

    total_concluded = sum(len(evts) for evts in concluded_by_review_id.values())
    total_audit_reviews = sum(len(evts) for evts in audit_by_review_id.values())

    matched_pairs = 0
    issues: list[ConsistencyIssue] = []

    all_review_ids = list(
        dict.fromkeys(
            [*concluded_by_review_id.keys(), *audit_by_review_id.keys()]
        )
    )

    for review_id in all_review_ids:
        concluded_list = concluded_by_review_id.get(review_id, [])
        audit_list = audit_by_review_id.get(review_id, [])

        is_lifecycle_duplicate = len(concluded_list) > 1
        is_audit_duplicate = len(audit_list) > 1

        if is_lifecycle_duplicate:
            issues.append(
                ConsistencyIssue(
                    issue_type=ConsistencyIssueType.DUPLICATE_REVIEW_ID_IN_LIFECYCLE,
                    review_id=review_id,
                    workflow_id=None,
                    audit_event_id=None,
                    details=(
                        f"Duplicate review_id '{review_id}' in lifecycle: "
                        f"found {len(concluded_list)} WorkflowConcluded events"
                    ),
                )
            )

        if is_audit_duplicate:
            issues.append(
                ConsistencyIssue(
                    issue_type=ConsistencyIssueType.DUPLICATE_REVIEW_ID_IN_AUDIT,
                    review_id=review_id,
                    workflow_id=None,
                    audit_event_id=None,
                    details=(
                        f"Duplicate review_id '{review_id}' in audit: "
                        f"found {len(audit_list)} AuditEvent records"
                    ),
                )
            )

        if is_lifecycle_duplicate or is_audit_duplicate:
            continue

        if len(concluded_list) == 1 and len(audit_list) == 1:
            matched_pairs += 1
            concluded = concluded_list[0]
            audit_event = audit_list[0]

            if concluded.review.material_id != audit_event.material_id:
                issues.append(
                    ConsistencyIssue(
                        issue_type=ConsistencyIssueType.MATERIAL_ID_MISMATCH,
                        review_id=review_id,
                        workflow_id=concluded.workflow_id,
                        audit_event_id=audit_event.event_id,
                        details=(
                            f"Material ID mismatch for review_id '{review_id}': "
                            f"lifecycle has '{concluded.review.material_id}', "
                            f"audit has '{audit_event.material_id}'"
                        ),
                    )
                )

            if concluded.review.reviewer_id != audit_event.actor_id:
                issues.append(
                    ConsistencyIssue(
                        issue_type=ConsistencyIssueType.ACTOR_ID_MISMATCH,
                        review_id=review_id,
                        workflow_id=concluded.workflow_id,
                        audit_event_id=audit_event.event_id,
                        details=(
                            f"Actor ID mismatch for review_id '{review_id}': "
                            f"lifecycle has '{concluded.review.reviewer_id}', "
                            f"audit has '{audit_event.actor_id}'"
                        ),
                    )
                )

            if concluded.review.reviewed_at != audit_event.occurred_at:
                issues.append(
                    ConsistencyIssue(
                        issue_type=ConsistencyIssueType.TIMESTAMP_MISMATCH,
                        review_id=review_id,
                        workflow_id=concluded.workflow_id,
                        audit_event_id=audit_event.event_id,
                        details=(
                            f"Timestamp mismatch for review_id '{review_id}': "
                            f"lifecycle reviewed_at '{concluded.review.reviewed_at.isoformat()}', "
                            f"audit occurred_at '{audit_event.occurred_at.isoformat()}'"
                        ),
                    )
                )

            metadata = audit_event.metadata or {}
            expected_scalars: list[tuple[str, Any]] = [
                (
                    "system_recommendation",
                    concluded.review.system_recommendation.value,
                ),
                (
                    "human_decision",
                    concluded.review.human_decision.value,
                ),
                (
                    "agrees_with_system",
                    concluded.review.agrees_with_system,
                ),
                (
                    "correction_count",
                    len(concluded.review.corrections),
                ),
                (
                    "identity_provider",
                    concluded.review.reviewer_identity.identity_provider,
                ),
                (
                    "identity_subject",
                    concluded.review.reviewer_identity.identity_subject,
                ),
                (
                    "identity_verification_id",
                    concluded.review.reviewer_identity.verification_id,
                ),
            ]

            for field_name, expected_val in expected_scalars:
                if field_name not in metadata:
                    issues.append(
                        ConsistencyIssue(
                            issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                            review_id=review_id,
                            workflow_id=concluded.workflow_id,
                            audit_event_id=audit_event.event_id,
                            details=f"Metadata key '{field_name}' is missing in AuditEvent",
                        )
                    )
                else:
                    actual_val = metadata.get(field_name)
                    if type(actual_val) is not type(expected_val) or actual_val != expected_val:
                        issues.append(
                            ConsistencyIssue(
                                issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                                review_id=review_id,
                                workflow_id=concluded.workflow_id,
                                audit_event_id=audit_event.event_id,
                                details=(
                                    f"Metadata field '{field_name}' mismatch: "
                                    f"expected {expected_val!r}, got {actual_val!r}"
                                ),
                            )
                        )

            if "identity_verified_at" not in metadata:
                issues.append(
                    ConsistencyIssue(
                        issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                        review_id=review_id,
                        workflow_id=concluded.workflow_id,
                        audit_event_id=audit_event.event_id,
                        details="Metadata key 'identity_verified_at' is missing in AuditEvent",
                    )
                )
            else:
                raw_verified_at = metadata.get("identity_verified_at")
                if not isinstance(raw_verified_at, str):
                    issues.append(
                        ConsistencyIssue(
                            issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                            review_id=review_id,
                            workflow_id=concluded.workflow_id,
                            audit_event_id=audit_event.event_id,
                            details=(
                                f"Metadata field 'identity_verified_at' has invalid type: "
                                f"expected str, got {type(raw_verified_at).__name__}"
                            ),
                        )
                    )
                else:
                    try:
                        parsed_dt = datetime.fromisoformat(raw_verified_at)
                    except (ValueError, TypeError):
                        issues.append(
                            ConsistencyIssue(
                                issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                                review_id=review_id,
                                workflow_id=concluded.workflow_id,
                                audit_event_id=audit_event.event_id,
                                details=(
                                    f"Metadata field 'identity_verified_at' is not a valid ISO-8601 string: "
                                    f"{raw_verified_at!r}"
                                ),
                            )
                        )
                    else:
                        if parsed_dt.tzinfo is None or parsed_dt.utcoffset() is None:
                            issues.append(
                                ConsistencyIssue(
                                    issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                                    review_id=review_id,
                                    workflow_id=concluded.workflow_id,
                                    audit_event_id=audit_event.event_id,
                                    details=(
                                        f"Metadata field 'identity_verified_at' is naive (missing timezone): "
                                        f"{raw_verified_at!r}"
                                    ),
                                )
                            )
                        elif parsed_dt != concluded.review.reviewer_identity.verified_at:
                            issues.append(
                                ConsistencyIssue(
                                    issue_type=ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                                    review_id=review_id,
                                    workflow_id=concluded.workflow_id,
                                    audit_event_id=audit_event.event_id,
                                    details=(
                                        f"Metadata field 'identity_verified_at' mismatch: "
                                        f"expected {concluded.review.reviewer_identity.verified_at.isoformat()}, "
                                        f"got {parsed_dt.isoformat()}"
                                    ),
                                )
                            )
        elif len(concluded_list) == 1 and len(audit_list) == 0:
            concluded = concluded_list[0]
            issues.append(
                ConsistencyIssue(
                    issue_type=ConsistencyIssueType.MISSING_AUDIT_EVENT,
                    review_id=review_id,
                    workflow_id=concluded.workflow_id,
                    audit_event_id=None,
                    details=(
                        f"WorkflowConcluded for review_id '{review_id}' in "
                        f"workflow '{concluded.workflow_id}' has no corresponding AuditEvent"
                    ),
                )
            )
        elif len(concluded_list) == 0 and len(audit_list) == 1:
            audit_event = audit_list[0]
            issues.append(
                ConsistencyIssue(
                    issue_type=ConsistencyIssueType.MISSING_WORKFLOW_CONCLUDED,
                    review_id=review_id,
                    workflow_id=None,
                    audit_event_id=audit_event.event_id,
                    details=(
                        f"AuditEvent '{audit_event.event_id}' for review_id "
                        f"'{review_id}' has no corresponding WorkflowConcluded"
                    ),
                )
            )

    return DualWriteConsistencyReport(
        total_concluded_events=total_concluded,
        total_audit_review_events=total_audit_reviews,
        matched_pairs_count=matched_pairs,
        issues=tuple(issues),
    )


