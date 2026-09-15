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


@dataclass(frozen=True, slots=True)
class DecisionRecommendationEvaluationReport:
    """Relatório estruturado e imutável da avaliação de um conjunto de recomendações."""

    dataset_id: str
    cases: tuple[DecisionRecommendationCaseEvaluation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _normalize_required_text(self.dataset_id, "dataset_id"),
        )

        if not isinstance(self.cases, tuple):
            raise TypeError("cases must be a tuple")

        seen_case_ids: set[str] = set()
        for idx, item in enumerate(self.cases):
            if not isinstance(item, DecisionRecommendationCaseEvaluation):
                raise TypeError(
                    f"cases[{idx}] must be a DecisionRecommendationCaseEvaluation instance"
                )
            if item.evaluation_case_id in seen_case_ids:
                raise ValueError(
                    f"duplicate evaluation_case_id in cases: {item.evaluation_case_id!r}"
                )
            seen_case_ids.add(item.evaluation_case_id)

        canonical = tuple(
            sorted(
                self.cases,
                key=lambda c: (c.evaluation_case_id, c.ground_truth_id),
            )
        )
        object.__setattr__(self, "cases", canonical)

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def matched_cases(self) -> int:
        return sum(1 for c in self.cases if c.is_match)

    @property
    def mismatched_cases(self) -> int:
        return self.total_cases - self.matched_cases

    @property
    def accuracy(self) -> float | None:
        if self.total_cases == 0:
            return None
        return self.matched_cases / self.total_cases

    @property
    def is_empty(self) -> bool:
        return self.total_cases == 0

    @property
    def is_perfect_match(self) -> bool:
        return self.total_cases > 0 and self.matched_cases == self.total_cases

    @property
    def matches(self) -> tuple[DecisionRecommendationCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_match)

    @property
    def mismatches(self) -> tuple[DecisionRecommendationCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_mismatch)


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
