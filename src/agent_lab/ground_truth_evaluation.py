"""Camada de avaliação pura de Ground Truth no Agent Lab Pascoal."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueType
from agent_lab.ground_truth import (
    DecisionRecommendationGroundTruth,
    DecisionRecommendationGroundTruthDataset,
    DuplicatePairGroundTruth,
    DuplicatePairGroundTruthDataset,
    MaterialRuleGroundTruth,
    MaterialRuleGroundTruthDataset,
)


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


def evaluate_decision_recommendations(
    dataset: DecisionRecommendationGroundTruthDataset,
    predictions: Mapping[str, DecisionRecommendation],
) -> DecisionRecommendationEvaluationReport:
    """Avalia em lote um mapeamento de predições indexado por evaluation_case_id contra um dataset."""
    if not isinstance(dataset, DecisionRecommendationGroundTruthDataset):
        raise TypeError("dataset must be a DecisionRecommendationGroundTruthDataset")

    if not isinstance(predictions, Mapping):
        raise TypeError("predictions must be a Mapping[str, DecisionRecommendation]")

    for case_id, pred in predictions.items():
        if not isinstance(case_id, str) or isinstance(case_id, bool):
            raise TypeError(f"prediction key {case_id!r} must be a str")
        if not isinstance(pred, DecisionRecommendation):
            raise TypeError(
                f"prediction value for evaluation_case_id {case_id!r} "
                f"must be a DecisionRecommendation, got {type(pred).__name__}"
            )

    expected_case_ids = {item.evaluation_case_id for item in dataset.items}
    provided_case_ids = set(predictions.keys())

    missing = expected_case_ids - provided_case_ids
    if missing:
        raise ValueError(
            f"missing predictions for evaluation_case_id: {sorted(missing)!r}"
        )

    extra = provided_case_ids - expected_case_ids
    if extra:
        raise ValueError(
            f"unexpected predictions for evaluation_case_id: {sorted(extra)!r}"
        )

    evaluated_cases: list[DecisionRecommendationCaseEvaluation] = []
    for item in dataset.items:
        prediction = predictions[item.evaluation_case_id]
        if prediction.material_id != item.material_id:
            raise ValueError(
                f"material_id mismatch for evaluation_case_id {item.evaluation_case_id!r}: "
                f"prediction has {prediction.material_id!r}, ground truth has {item.material_id!r}"
            )
        evaluated_case = evaluate_decision_recommendation(item, prediction)
        evaluated_cases.append(evaluated_case)

    return DecisionRecommendationEvaluationReport(
        dataset_id=dataset.dataset_id,
        cases=tuple(evaluated_cases),
    )


def _validate_and_canonicalize_issue_types(
    value: object,
    field_name: str,
) -> tuple[IssueType, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")

    for item in value:
        if not isinstance(item, IssueType):
            raise TypeError(
                f"{field_name} must contain only IssueType instances"
            )

    if IssueType.POSSIBLE_DUPLICATE in value:
        raise ValueError(
            f"POSSIBLE_DUPLICATE is not permitted in {field_name}"
        )

    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must not contain duplicates")

    return tuple(sorted(value, key=lambda item: item.value))


@dataclass(frozen=True, slots=True)
class MaterialRulePrediction:
    """Predição de regras cadastrais de materiais associada a um material_id."""

    material_id: str
    predicted_issue_types: tuple[IssueType, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "material_id",
            _normalize_required_text(self.material_id, "material_id"),
        )
        canonical = _validate_and_canonicalize_issue_types(
            self.predicted_issue_types,
            "predicted_issue_types",
        )
        object.__setattr__(self, "predicted_issue_types", canonical)


@dataclass(frozen=True, slots=True)
class MaterialRuleCaseEvaluation:
    """Resultado imutável da avaliação de regras cadastrais de um caso individual."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_issue_types: tuple[IssueType, ...]
    predicted_issue_types: tuple[IssueType, ...]

    def __post_init__(self) -> None:
        text_fields = ("evaluation_case_id", "ground_truth_id", "material_id")
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(getattr(self, field_name), field_name),
            )

        canonical_expected = _validate_and_canonicalize_issue_types(
            self.expected_issue_types,
            "expected_issue_types",
        )
        object.__setattr__(self, "expected_issue_types", canonical_expected)

        canonical_predicted = _validate_and_canonicalize_issue_types(
            self.predicted_issue_types,
            "predicted_issue_types",
        )
        object.__setattr__(self, "predicted_issue_types", canonical_predicted)

    @property
    def is_match(self) -> bool:
        return self.predicted_issue_types == self.expected_issue_types

    @property
    def is_mismatch(self) -> bool:
        return not self.is_match

    @property
    def false_positives(self) -> tuple[IssueType, ...]:
        expected_set = set(self.expected_issue_types)
        fp = [item for item in self.predicted_issue_types if item not in expected_set]
        return tuple(sorted(fp, key=lambda item: item.value))

    @property
    def false_negatives(self) -> tuple[IssueType, ...]:
        predicted_set = set(self.predicted_issue_types)
        fn = [item for item in self.expected_issue_types if item not in predicted_set]
        return tuple(sorted(fn, key=lambda item: item.value))

    @property
    def true_positives(self) -> tuple[IssueType, ...]:
        expected_set = set(self.expected_issue_types)
        tp = [item for item in self.predicted_issue_types if item in expected_set]
        return tuple(sorted(tp, key=lambda item: item.value))

    @property
    def has_false_positives(self) -> bool:
        return len(self.false_positives) > 0

    @property
    def has_false_negatives(self) -> bool:
        return len(self.false_negatives) > 0

    @property
    def is_clean_match(self) -> bool:
        return self.is_match and len(self.expected_issue_types) == 0

    @property
    def is_defect_match(self) -> bool:
        return self.is_match and len(self.expected_issue_types) > 0


@dataclass(frozen=True, slots=True)
class MaterialRuleEvaluationReport:
    """Relatório estruturado e imutável da avaliação em lote de regras cadastrais."""

    dataset_id: str
    cases: tuple[MaterialRuleCaseEvaluation, ...]

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
            if not isinstance(item, MaterialRuleCaseEvaluation):
                raise TypeError(
                    f"cases[{idx}] must be a MaterialRuleCaseEvaluation instance"
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
    def exact_match_ratio(self) -> float | None:
        return self.accuracy

    @property
    def total_false_positives(self) -> int:
        return sum(len(c.false_positives) for c in self.cases)

    @property
    def total_false_negatives(self) -> int:
        return sum(len(c.false_negatives) for c in self.cases)

    @property
    def total_true_positives(self) -> int:
        return sum(len(c.true_positives) for c in self.cases)

    @property
    def is_empty(self) -> bool:
        return self.total_cases == 0

    @property
    def is_perfect_match(self) -> bool:
        return self.total_cases > 0 and self.matched_cases == self.total_cases

    @property
    def matches(self) -> tuple[MaterialRuleCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_match)

    @property
    def mismatches(self) -> tuple[MaterialRuleCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_mismatch)


def evaluate_material_rule(
    ground_truth: MaterialRuleGroundTruth,
    prediction: MaterialRulePrediction,
) -> MaterialRuleCaseEvaluation:
    """Compara deterministicamente uma predição de regras contra um gabarito individual."""
    if not isinstance(ground_truth, MaterialRuleGroundTruth):
        raise TypeError("ground_truth must be a MaterialRuleGroundTruth")

    if not isinstance(prediction, MaterialRulePrediction):
        raise TypeError("prediction must be a MaterialRulePrediction")

    if prediction.material_id != ground_truth.material_id:
        raise ValueError(
            f"material_id mismatch: prediction has {prediction.material_id!r}, "
            f"ground_truth has {ground_truth.material_id!r}"
        )

    return MaterialRuleCaseEvaluation(
        evaluation_case_id=ground_truth.evaluation_case_id,
        ground_truth_id=ground_truth.ground_truth_id,
        material_id=ground_truth.material_id,
        expected_issue_types=ground_truth.expected_issue_types,
        predicted_issue_types=prediction.predicted_issue_types,
    )


def evaluate_material_rules(
    dataset: MaterialRuleGroundTruthDataset,
    predictions: Mapping[str, MaterialRulePrediction],
) -> MaterialRuleEvaluationReport:
    """Avalia em lote um mapeamento de predições indexado por evaluation_case_id contra um dataset de regras."""
    if not isinstance(dataset, MaterialRuleGroundTruthDataset):
        raise TypeError("dataset must be a MaterialRuleGroundTruthDataset")

    if not isinstance(predictions, Mapping):
        raise TypeError("predictions must be a Mapping[str, MaterialRulePrediction]")

    for case_id, pred in predictions.items():
        if not isinstance(case_id, str) or isinstance(case_id, bool):
            raise TypeError(f"prediction key {case_id!r} must be a str")
        if not isinstance(pred, MaterialRulePrediction):
            raise TypeError(
                f"prediction value for evaluation_case_id {case_id!r} "
                f"must be a MaterialRulePrediction, got {type(pred).__name__}"
            )

    expected_case_ids = {item.evaluation_case_id for item in dataset.items}
    provided_case_ids = set(predictions.keys())

    missing = expected_case_ids - provided_case_ids
    if missing:
        raise ValueError(
            f"missing predictions for evaluation_case_id: {sorted(missing)!r}"
        )

    extra = provided_case_ids - expected_case_ids
    if extra:
        raise ValueError(
            f"unexpected predictions for evaluation_case_id: {sorted(extra)!r}"
        )

    evaluated_cases: list[MaterialRuleCaseEvaluation] = []
    for item in dataset.items:
        prediction = predictions[item.evaluation_case_id]
        if prediction.material_id != item.material_id:
            raise ValueError(
                f"material_id mismatch for evaluation_case_id {item.evaluation_case_id!r}: "
                f"prediction has {prediction.material_id!r}, ground truth has {item.material_id!r}"
            )
        evaluated_case = evaluate_material_rule(item, prediction)
        evaluated_cases.append(evaluated_case)

    return MaterialRuleEvaluationReport(
        dataset_id=dataset.dataset_id,
        cases=tuple(evaluated_cases),
    )


@dataclass(frozen=True, slots=True)
class DuplicatePairPrediction:
    """Predição binária de duplicidade sobre um par canônico de materiais."""

    material_id_a: str
    material_id_b: str
    is_duplicate: bool

    def __post_init__(self) -> None:
        normalized_a = _normalize_required_text(self.material_id_a, "material_id_a")
        normalized_b = _normalize_required_text(self.material_id_b, "material_id_b")

        object.__setattr__(self, "material_id_a", normalized_a)
        object.__setattr__(self, "material_id_b", normalized_b)

        if self.material_id_a == self.material_id_b:
            raise ValueError(
                "material_id_a and material_id_b must be different"
            )

        if self.material_id_a > self.material_id_b:
            raise ValueError(
                "material_id_a must be less than material_id_b"
            )

        if not isinstance(self.is_duplicate, bool):
            raise TypeError("is_duplicate must be a bool")


@dataclass(frozen=True, slots=True)
class DuplicatePairCaseEvaluation:
    """Resultado imutável da avaliação de duplicidade de um par individual de materiais."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id_a: str
    material_id_b: str
    expected_is_duplicate: bool
    predicted_is_duplicate: bool

    def __post_init__(self) -> None:
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id_a",
            "material_id_b",
        )
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(getattr(self, field_name), field_name),
            )

        if not isinstance(self.expected_is_duplicate, bool):
            raise TypeError("expected_is_duplicate must be a bool")

        if not isinstance(self.predicted_is_duplicate, bool):
            raise TypeError("predicted_is_duplicate must be a bool")

    @property
    def is_match(self) -> bool:
        return self.predicted_is_duplicate == self.expected_is_duplicate

    @property
    def is_mismatch(self) -> bool:
        return not self.is_match


@dataclass(frozen=True, slots=True)
class DuplicatePairEvaluationReport:
    """Relatório estruturado e imutável da avaliação de pares duplicados."""

    dataset_id: str
    cases: tuple[DuplicatePairCaseEvaluation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _normalize_required_text(
                self.dataset_id,
                "dataset_id",
            ),
        )

        if not isinstance(self.cases, tuple):
            raise TypeError("cases must be a tuple")

        seen_case_ids: set[str] = set()
        for idx, item in enumerate(self.cases):
            if not isinstance(
                item,
                DuplicatePairCaseEvaluation,
            ):
                raise TypeError(
                    f"cases[{idx}] must be a "
                    f"DuplicatePairCaseEvaluation instance"
                )

            if item.evaluation_case_id in seen_case_ids:
                raise ValueError(
                    "duplicate evaluation_case_id in cases: "
                    f"{item.evaluation_case_id!r}"
                )

            seen_case_ids.add(item.evaluation_case_id)

        canonical = tuple(
            sorted(
                self.cases,
                key=lambda case: (
                    case.evaluation_case_id,
                    case.ground_truth_id,
                ),
            )
        )
        object.__setattr__(
            self,
            "cases",
            canonical,
        )

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def matched_cases(self) -> int:
        return sum(
            1
            for case in self.cases
            if case.is_match
        )

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
        return (
            self.total_cases > 0
            and self.matched_cases == self.total_cases
        )

    @property
    def matches(
        self,
    ) -> tuple[DuplicatePairCaseEvaluation, ...]:
        return tuple(
            case
            for case in self.cases
            if case.is_match
        )

    @property
    def mismatches(
        self,
    ) -> tuple[DuplicatePairCaseEvaluation, ...]:
        return tuple(
            case
            for case in self.cases
            if case.is_mismatch
        )


def evaluate_duplicate_pair(
    ground_truth: DuplicatePairGroundTruth,
    prediction: DuplicatePairPrediction,
) -> DuplicatePairCaseEvaluation:
    """Compara deterministicamente uma predição contra um gabarito individual de par de duplicata."""
    if not isinstance(ground_truth, DuplicatePairGroundTruth):
        raise TypeError("ground_truth must be a DuplicatePairGroundTruth")

    if not isinstance(prediction, DuplicatePairPrediction):
        raise TypeError("prediction must be a DuplicatePairPrediction")

    if (
        prediction.material_id_a != ground_truth.material_id_a
        or prediction.material_id_b != ground_truth.material_id_b
    ):
        raise ValueError(
            f"material pair mismatch: prediction has "
            f"({prediction.material_id_a!r}, {prediction.material_id_b!r}), "
            f"ground_truth has "
            f"({ground_truth.material_id_a!r}, {ground_truth.material_id_b!r})"
        )

    return DuplicatePairCaseEvaluation(
        evaluation_case_id=ground_truth.evaluation_case_id,
        ground_truth_id=ground_truth.ground_truth_id,
        material_id_a=ground_truth.material_id_a,
        material_id_b=ground_truth.material_id_b,
        expected_is_duplicate=ground_truth.is_duplicate,
        predicted_is_duplicate=prediction.is_duplicate,
    )


def evaluate_duplicate_pairs(
    dataset: DuplicatePairGroundTruthDataset,
    predictions: Mapping[str, DuplicatePairPrediction],
) -> DuplicatePairEvaluationReport:
    """Avalia em lote um mapeamento de predições indexado por evaluation_case_id contra um dataset de duplicatas."""
    if not isinstance(
        dataset,
        DuplicatePairGroundTruthDataset,
    ):
        raise TypeError(
            "dataset must be a DuplicatePairGroundTruthDataset"
        )

    if not isinstance(predictions, Mapping):
        raise TypeError(
            "predictions must be a Mapping[str, DuplicatePairPrediction]"
        )

    for case_id, prediction in predictions.items():
        if (
            not isinstance(case_id, str)
            or isinstance(case_id, bool)
        ):
            raise TypeError(
                f"prediction key {case_id!r} must be a str"
            )
        if not isinstance(
            prediction,
            DuplicatePairPrediction,
        ):
            raise TypeError(
                f"prediction value for evaluation_case_id "
                f"{case_id!r} must be a DuplicatePairPrediction, "
                f"got {type(prediction).__name__}"
            )

    expected_case_ids = {
        item.evaluation_case_id
        for item in dataset.items
    }

    provided_case_ids = set(
        predictions.keys()
    )

    missing = (
        expected_case_ids
        - provided_case_ids
    )

    if missing:
        raise ValueError(
            f"missing predictions for evaluation_case_id: "
            f"{sorted(missing)!r}"
        )

    extra = (
        provided_case_ids
        - expected_case_ids
    )

    if extra:
        raise ValueError(
            f"unexpected predictions for evaluation_case_id: "
            f"{sorted(extra)!r}"
        )

    evaluated_cases: list[
        DuplicatePairCaseEvaluation
    ] = []

    for item in dataset.items:
        prediction = predictions[
            item.evaluation_case_id
        ]

        evaluated_case = evaluate_duplicate_pair(
            item,
            prediction,
        )

        evaluated_cases.append(
            evaluated_case
        )

    return DuplicatePairEvaluationReport(
        dataset_id=dataset.dataset_id,
        cases=tuple(evaluated_cases),
    )
