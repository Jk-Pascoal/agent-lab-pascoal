"""Camada de avaliação pura de Ground Truth no Agent Lab Pascoal."""

from __future__ import annotations

from dataclasses import dataclass

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.ground_truth import DecisionRecommendationGroundTruth


def _normalize_required_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a str")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty or whitespace")

    return normalized


@dataclass(frozen=True, slots=True)
class DecisionRecommendationCaseEvaluation:
    """Resultado imutável da avaliação determinística de um caso individual."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_decision: GovernanceDecision
    predicted_decision: GovernanceDecision

    def __post_init__(self) -> None:
        text_fields = ("evaluation_case_id", "ground_truth_id", "material_id")
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(getattr(self, field_name), field_name),
            )

        if not isinstance(self.expected_decision, GovernanceDecision):
            raise TypeError("expected_decision must be a GovernanceDecision")

        if not isinstance(self.predicted_decision, GovernanceDecision):
            raise TypeError("predicted_decision must be a GovernanceDecision")

    @property
    def is_match(self) -> bool:
        return self.predicted_decision == self.expected_decision

    @property
    def is_mismatch(self) -> bool:
        return not self.is_match


def evaluate_decision_recommendation(
    ground_truth: DecisionRecommendationGroundTruth,
    prediction: DecisionRecommendation,
) -> DecisionRecommendationCaseEvaluation:
    """Compara deterministicamente uma predição contra um gabarito individual."""
    if not isinstance(ground_truth, DecisionRecommendationGroundTruth):
        raise TypeError("ground_truth must be a DecisionRecommendationGroundTruth")

    if not isinstance(prediction, DecisionRecommendation):
        raise TypeError("prediction must be a DecisionRecommendation")

    if prediction.material_id != ground_truth.material_id:
        raise ValueError(
            f"material_id mismatch: prediction has {prediction.material_id!r}, "
            f"ground_truth has {ground_truth.material_id!r}"
        )

    return DecisionRecommendationCaseEvaluation(
        evaluation_case_id=ground_truth.evaluation_case_id,
        ground_truth_id=ground_truth.ground_truth_id,
        material_id=ground_truth.material_id,
        expected_decision=ground_truth.expected_recommendation,
        predicted_decision=prediction.decision,
    )
