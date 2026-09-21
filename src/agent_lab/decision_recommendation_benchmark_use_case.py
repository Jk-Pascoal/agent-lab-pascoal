"""Caso de uso de benchmark para recomendações de governança."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .decision import (
    DecisionRecommendation,
    recommend_decision,
)
from .domain import MaterialRecord
from .ground_truth import DecisionRecommendationGroundTruthDataset
from .ground_truth_evaluation import (
    DecisionRecommendationEvaluationReport,
    evaluate_decision_recommendations,
)
from .validator import DeterministicGovernanceValidator

RecommendationPipeline = Callable[[MaterialRecord], DecisionRecommendation]


def _default_deterministic_pipeline(
    material: MaterialRecord,
) -> DecisionRecommendation:
    assessment = DeterministicGovernanceValidator().analyze(material)

    if assessment.evidence_collection is None:
        raise ValueError(
            "deterministic governance assessment must contain evidence_collection"
        )

    return recommend_decision(
        assessment.evidence_collection
    )


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
        pipeline: RecommendationPipeline | None = None,
    ) -> None:
        self._pipeline = (
            pipeline
            if pipeline is not None
            else _default_deterministic_pipeline
        )

    def execute(
        self,
        dataset: DecisionRecommendationGroundTruthDataset,
        cases: Sequence[DecisionRecommendationBenchmarkCase],
    ) -> DecisionRecommendationEvaluationReport:
        if not isinstance(dataset, DecisionRecommendationGroundTruthDataset):
            raise TypeError("dataset must be a DecisionRecommendationGroundTruthDataset")

        if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
            raise TypeError("cases must be a Sequence, excluding str and bytes")

        for case in cases:
            if not isinstance(case, DecisionRecommendationBenchmarkCase):
                raise TypeError(
                    "all items in cases must be DecisionRecommendationBenchmarkCase instances"
                )

        seen_case_ids: set[str] = set()
        for case in cases:
            if case.evaluation_case_id in seen_case_ids:
                raise ValueError(
                    f"duplicate evaluation_case_id in cases: {case.evaluation_case_id!r}"
                )
            seen_case_ids.add(case.evaluation_case_id)

        predictions: dict[str, DecisionRecommendation] = {}

        for case in cases:
            prediction = self._pipeline(case.material)

            if not isinstance(prediction, DecisionRecommendation):
                raise TypeError(
                    f"pipeline return must be a DecisionRecommendation, got {type(prediction).__name__}"
                )

            if prediction.material_id != case.material.material_id:
                raise ValueError(
                    f"prediction.material_id mismatch: expected {case.material.material_id!r}, "
                    f"got {prediction.material_id!r}"
                )

            predictions[case.evaluation_case_id] = prediction

        return evaluate_decision_recommendations(
            dataset,
            predictions,
        )
