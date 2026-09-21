"""Caso de uso de benchmark para recomendações de governança."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import MaterialRecord


@dataclass(frozen=True, slots=True)
class DecisionRecommendationBenchmarkCase:
    """Caso experimental que associa uma identidade de teste ao registro a ser processado."""

    evaluation_case_id: str
    material: MaterialRecord

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case_id, str) or isinstance(
            self.evaluation_case_id, bool
        ):
            raise TypeError("evaluation_case_id must be a str")

        if (
            not self.evaluation_case_id
            or self.evaluation_case_id != self.evaluation_case_id.strip()
        ):
            raise ValueError(
                "evaluation_case_id must be a non-empty canonical string without outer whitespace"
            )

        if not isinstance(self.material, MaterialRecord):
            raise TypeError("material must be a MaterialRecord")
