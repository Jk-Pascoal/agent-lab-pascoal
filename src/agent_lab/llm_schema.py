"""Contrato estruturado para respostas produzidas por agentes com LLM."""

from pydantic import BaseModel, ConfigDict, Field

from .domain import GovernanceDecision, IssueType


class GovernanceAgentOutput(BaseModel):
    """Saída validada antes de entrar no domínio da aplicação."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    material_id: str = Field(min_length=1)
    decision: GovernanceDecision
    confidence: float = Field(ge=0.0, le=1.0)
    issues: tuple[IssueType, ...]
    summary: str = Field(min_length=1)
    evidence: tuple[str, ...]


def parse_governance_agent_output(
    raw_json: str,
) -> GovernanceAgentOutput:
    """Converte JSON bruto em uma saída validada do agente."""
    return GovernanceAgentOutput.model_validate_json(raw_json)


def governance_agent_output_schema() -> dict[str, object]:
    """Exporta o contrato do agente no formato JSON Schema."""
    return GovernanceAgentOutput.model_json_schema()