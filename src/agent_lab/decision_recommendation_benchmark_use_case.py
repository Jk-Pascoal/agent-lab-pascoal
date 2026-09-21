"""Caso de uso de benchmark para recomendações de governança."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .decision import DecisionRecommendation
from .domain import MaterialRecord
from .ground_truth import DecisionRecommendationGroundTruthDataset
from .ground_truth_evaluation import (
    DecisionRecommendationEvaluationReport,
    evaluate_decision_recommendations,
)

RecommendationPipeline = Callable[[MaterialRecord], DecisionRecommendation]


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


class RunDecisionRecommendationBenchmarkUseCase:
    """Caso de uso para execução e avaliação de benchmark de recomendação de governança."""

    def __init__(
        self,
        pipeline: RecommendationPipeline,
    ) -> None:
        self._pipeline = pipeline

    def execute(
        self,
        dataset: DecisionRecommendationGroundTruthDataset,
        cases: Sequence[DecisionRecommendationBenchmarkCase],
    ) -> DecisionRecommendationEvaluationReport:
        predictions: dict[str, DecisionRecommendation] = {}

        for case in cases:
            prediction = self._pipeline(case.material)
            predictions[case.evaluation_case_id] = prediction

        return evaluate_decision_recommendations(
            dataset,
            predictions,
        )
