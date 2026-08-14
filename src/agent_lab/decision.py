"""Pipeline determinístico entre evidências e recomendação de governança."""

from dataclasses import dataclass

from .domain import GovernanceDecision, IssueSeverity
from .evidence import EvidenceCollection, GovernanceEvidence


@dataclass(frozen=True, slots=True)
class DecisionRecommendation:
    """Recomendação explicável do sistema, sujeita à decisão humana final."""

    material_id: str
    decision: GovernanceDecision
    evidence: tuple[GovernanceEvidence, ...]
    rationale: str
    requires_human_decision: bool = True

    def __post_init__(self) -> None:
        if self.material_id == "":
            raise ValueError("material_id não pode ser vazio")

        if not isinstance(self.decision, GovernanceDecision):
            raise ValueError("decision deve ser um GovernanceDecision válido")

        if self.rationale == "":
            raise ValueError("rationale não pode ser vazio")

        if self.requires_human_decision is not True:
            raise ValueError("a recomendação exige decisão humana final")


def _decision_for(
    evidence: tuple[GovernanceEvidence, ...],
) -> GovernanceDecision:
    if any(item.severity is IssueSeverity.BLOCKING for item in evidence):
        return GovernanceDecision.REJECT

    if evidence:
        return GovernanceDecision.REVIEW

    return GovernanceDecision.APPROVE


def _rationale_for(
    decision: GovernanceDecision,
    evidence: tuple[GovernanceEvidence, ...],
) -> str:
    blocking_count = sum(
        item.severity is IssueSeverity.BLOCKING for item in evidence
    )
    review_count = len(evidence) - blocking_count

    if decision is GovernanceDecision.REJECT:
        return (
            "Recomendação REJECT: "
            f"{blocking_count} evidência(s) impeditiva(s) e "
            f"{review_count} evidência(s) revisável(is)."
        )

    if decision is GovernanceDecision.REVIEW:
        return (
            "Recomendação REVIEW: "
            f"{review_count} evidência(s) requer(em) análise humana."
        )

    return "Recomendação APPROVE: nenhuma evidência impeditiva ou revisável."


def recommend_decision(
    collection: EvidenceCollection,
) -> DecisionRecommendation:
    """Converte uma coleção validada em recomendação determinística."""

    if not isinstance(collection, EvidenceCollection):
        raise TypeError("collection deve ser uma EvidenceCollection")

    decision = _decision_for(collection.evidence)

    return DecisionRecommendation(
        material_id=collection.material_id,
        decision=decision,
        evidence=collection.evidence,
        rationale=_rationale_for(decision, collection.evidence),
    )
