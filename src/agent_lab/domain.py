"""Modelos de domínio independentes de framework e provedor de LLM."""

from dataclasses import dataclass, field
from enum import StrEnum


class GovernanceDecision(StrEnum):
    """Recomendação do sistema; nunca uma decisão final no MVP."""

    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class IssueSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class IssueType(StrEnum):
    MISSING_CRITICAL_FIELD = "MISSING_CRITICAL_FIELD"
    MISSING_TECHNICAL_ATTRIBUTE = "MISSING_TECHNICAL_ATTRIBUTE"
    INVALID_UNIT = "INVALID_UNIT"
    INVALID_STATUS = "INVALID_STATUS"
    SUSPICIOUS_UNIT = "SUSPICIOUS_UNIT"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    AMBIGUOUS_DESCRIPTION = "AMBIGUOUS_DESCRIPTION"
    CLASSIFICATION_CONFLICT = "CLASSIFICATION_CONFLICT"


@dataclass(frozen=True, slots=True)
class MaterialRecord:
    """Registro bruto.

    Campos vazios são aceitos porque o objetivo do sistema é justamente
    encontrar defeitos nos dados recebidos.
    """

    material_id: str
    description_short: str = ""
    long_description: str = ""
    unit: str = ""
    manufacturer: str = ""
    manufacturer_part_number: str = ""
    material_group: str = ""
    status: str = ""


@dataclass(frozen=True, slots=True)
class GovernanceIssue:
    issue_type: IssueType
    field_name: str
    message: str
    severity: IssueSeverity = IssueSeverity.WARNING


@dataclass(frozen=True, slots=True)
class GovernanceAssessment:
    material_id: str
    completeness: float
    confidence: float
    decision: GovernanceDecision
    normalized_description: str = ""
    suggested_group: str = ""
    issues: tuple[GovernanceIssue, ...] = field(default_factory=tuple)
    duplicate_candidates: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (
            ("completeness", self.completeness),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} deve estar entre 0 e 1")
