from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
