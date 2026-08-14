"""Contratos estruturados para evidências de governança."""

from dataclasses import dataclass
from enum import StrEnum

from .domain import GovernanceIssue, IssueSeverity, IssueType
from .llm_schema import GovernanceAgentOutput


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
    severity: IssueSeverity = IssueSeverity.WARNING

    def __post_init__(self) -> None:
        if self.material_id == "":
            raise ValueError("material_id não pode ser vazio")

        if not isinstance(self.source, EvidenceSource):
            raise ValueError("source deve ser um EvidenceSource válido")

        if not isinstance(self.issue_type, IssueType):
            raise ValueError("issue_type deve ser um IssueType válido")

        if self.observation == "":
            raise ValueError("observation não pode ser vazia")

        if not isinstance(self.severity, IssueSeverity):
            raise ValueError("severity deve ser um IssueSeverity válido")


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
            severity=issue.severity,
        )
        for issue in issues
    )

    return EvidenceCollection(
        material_id=material_id,
        evidence=evidence,
    )


def build_llm_evidence_collection(
    output: GovernanceAgentOutput,
) -> EvidenceCollection:
    """Transforma uma saída LLM validada em evidências estruturadas.

    A transformação preserva identidade, ordem e tipo das Issues, mas não
    promove ``decision`` ou ``confidence`` da LLM a decisão ou score de
    governança. Na v1, toda evidência proveniente da LLM recebe severidade
    ``WARNING``: ela pode recomendar revisão humana, mas nunca causar rejeição
    automática. Cada Issue deve possuir exatamente uma observação correspondente.
    """

    if len(output.issues) != len(output.evidence):
        raise ValueError(
            "issues e evidence da saída LLM devem possuir a mesma cardinalidade"
        )

    evidence = tuple(
        GovernanceEvidence(
            material_id=output.material_id,
            source=EvidenceSource.LLM,
            issue_type=issue_type,
            observation=observation,
            severity=IssueSeverity.WARNING,
        )
        for issue_type, observation in zip(
            output.issues,
            output.evidence,
            strict=True,
        )
    )

    return EvidenceCollection(
        material_id=output.material_id,
        evidence=evidence,
    )
