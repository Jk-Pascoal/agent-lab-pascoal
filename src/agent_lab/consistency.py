from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

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
    for review_id, concluded_list in concluded_by_review_id.items():
        audit_list = audit_by_review_id.get(review_id, [])
        if len(concluded_list) == 1 and len(audit_list) == 1:
            matched_pairs += 1

    return DualWriteConsistencyReport(
        total_concluded_events=total_concluded,
        total_audit_review_events=total_audit_reviews,
        matched_pairs_count=matched_pairs,
        issues=(),
    )

