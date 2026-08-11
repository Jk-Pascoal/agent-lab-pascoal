"""Contratos estruturados para evidências de governança."""

from dataclasses import dataclass
from enum import StrEnum

from .domain import IssueType


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
