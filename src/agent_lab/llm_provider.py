"""Contrato mínimo para provedores de LLM.

Este módulo define apenas a capacidade necessária pelo Agent Lab Pascoal.
Implementações concretas de fornecedores ficam fora desta camada.
"""

from typing import Protocol


class LLMProvider(Protocol):
    """Contrato estrutural para um provedor capaz de gerar JSON bruto."""

    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        """Gera uma resposta JSON bruta obedecendo ao schema esperado."""
        ...
