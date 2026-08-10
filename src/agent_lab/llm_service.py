"""Fronteira de execução da LLM para análise de materiais."""

from .domain import MaterialRecord
from .llm_provider import LLMProvider
from .llm_schema import (
    GovernanceAgentOutput,
    governance_agent_output_schema,
    parse_governance_agent_output,
)


def build_governance_prompt(material: MaterialRecord) -> str:
    """Constrói um prompt determinístico a partir de um registro de material."""
    return "\n".join(
        (
            "Analise o cadastro de material abaixo sob a perspectiva de governança PDM/BOM.",
            "A resposta deve obedecer estritamente ao JSON Schema fornecido pelo sistema.",
            "Não invente dados ausentes.",
            "A saída é uma recomendação auditável e deve permanecer sujeita à revisão humana.",
            "",
            "Material:",
            f"material_id: {material.material_id}",
            f"description_short: {material.description_short}",
            f"long_description: {material.long_description}",
            f"unit: {material.unit}",
            f"manufacturer: {material.manufacturer}",
            f"manufacturer_part_number: {material.manufacturer_part_number}",
            f"material_group: {material.material_group}",
            f"status: {material.status}",
        )
    )


def analyze_material(
    material: MaterialRecord,
    provider: LLMProvider,
) -> GovernanceAgentOutput:
    """Executa a fronteira LLM e retorna somente uma saída validada."""
    prompt = build_governance_prompt(material)
    response_schema = governance_agent_output_schema()

    raw_json = provider.generate(
        prompt=prompt,
        response_schema=response_schema,
    )

    return parse_governance_agent_output(raw_json)
