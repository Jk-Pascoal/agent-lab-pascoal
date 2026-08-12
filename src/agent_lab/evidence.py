"""Contratos estruturados para evidências de governança."""

from dataclasses import dataclass
from enum import StrEnum

from .domain import GovernanceIssue, IssueType


class EvidenceSource(StrEnum):
    """Origem lógica de uma evidência de governança."""

    RULE = "RULE"
    VALIDATION = "VALIDATION"
    DUPLICATE = "DUPLICATE"
    LLM = "LLM"


@dataclass(frozen=True, slots=True)
class GovernanceEvidence:
    """Representa uma observação estruturada sobre um material."""

    material_id: str
    source: EvidenceSource
    issue_type: IssueType
    observation: str

    def __post_init__(self) -> None:
        if self.material_id == "":
            raise ValueError("material_id não pode ser vazio")

        if not isinstance(self.source, EvidenceSource):
            raise ValueError("source deve ser um EvidenceSource válido")

        if not isinstance(self.issue_type, IssueType):
            raise ValueError("issue_type deve ser um IssueType válido")

        if self.observation == "":
            raise ValueError("observation não pode ser vazia")


@dataclass(frozen=True, slots=True)
class EvidenceCollection:
    """Agrupa evidências estruturadas de uma análise de material."""

    material_id: str
    evidence: tuple[GovernanceEvidence, ...]

    def __post_init__(self) -> None:
        if self.material_id == "":
            raise ValueError("material_id não pode ser vazio")

        for item in self.evidence:
            if item.material_id != self.material_id:
                raise ValueError(
                    "evidence material_id deve corresponder ao material_id da coleção"
                )


def _source_for_issue(issue: GovernanceIssue) -> EvidenceSource:
    """Resolve a proveniência controlada de uma GovernanceIssue."""

    if issue.issue_type is IssueType.POSSIBLE_DUPLICATE:
        return EvidenceSource.DUPLICATE

    return EvidenceSource.RULE


def build_evidence_collection(
    material_id: str,
    issues: tuple[GovernanceIssue, ...] | list[GovernanceIssue],
) -> EvidenceCollection:
    """Transforma Issues determinísticas em evidências estruturadas."""

    evidence = tuple(
        GovernanceEvidence(
            material_id=material_id,
            source=_source_for_issue(issue),
            issue_type=issue.issue_type,
            observation=issue.message,
        )
        for issue in issues
    )

    return EvidenceCollection(
        material_id=material_id,
        evidence=evidence,
    )
