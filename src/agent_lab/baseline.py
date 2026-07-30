"""Avaliação do baseline contra os rótulos sintéticos."""

from collections import Counter
from dataclasses import dataclass

from .data_io import LabeledMaterial
from .domain import GovernanceAssessment, IssueType
from .validator import DeterministicGovernanceValidator


@dataclass(frozen=True, slots=True)
class BaselineReport:
    total: int
    correct: int
    label_hits: int
    exact_match_accuracy: float
    label_hit_rate: float
    duplicate_precision: float
    duplicate_recall: float
    decisions: dict[str, int]
    errors: tuple[str, ...]


def _predicted_labels(assessment: GovernanceAssessment) -> set[str]:
    if not assessment.issues:
        return {"VALID"}
    return {issue.issue_type.value for issue in assessment.issues}


def evaluate_baseline(
    materials: list[LabeledMaterial],
) -> tuple[list[GovernanceAssessment], BaselineReport]:
    records = [item.record for item in materials]
    assessments = DeterministicGovernanceValidator().analyze_all(records)

    correct = 0
    label_hits = 0
    errors: list[str] = []
    duplicate_tp = 0
    duplicate_fp = 0
    duplicate_fn = 0

    for item, assessment in zip(materials, assessments, strict=True):
        predicted = _predicted_labels(assessment)
        expected = item.expected_issue
        expected_set = {expected}
        if expected in predicted:
            label_hits += 1
        if predicted == expected_set:
            correct += 1
        else:
            errors.append(
                f"{item.record.material_id}: esperado={expected}, "
                f"previsto={sorted(predicted)}"
            )

        expected_duplicate = expected == IssueType.POSSIBLE_DUPLICATE.value
        predicted_duplicate = (
            IssueType.POSSIBLE_DUPLICATE.value in predicted
        )
        if expected_duplicate and predicted_duplicate:
            duplicate_tp += 1
        elif predicted_duplicate:
            duplicate_fp += 1
        elif expected_duplicate:
            duplicate_fn += 1

    total = len(materials)
    decisions = Counter(assessment.decision.value for assessment in assessments)
    precision_denominator = duplicate_tp + duplicate_fp
    recall_denominator = duplicate_tp + duplicate_fn

    report = BaselineReport(
        total=total,
        correct=correct,
        label_hits=label_hits,
        exact_match_accuracy=(correct / total) if total else 0.0,
        label_hit_rate=(label_hits / total) if total else 0.0,
        duplicate_precision=(
            duplicate_tp / precision_denominator if precision_denominator else 0.0
        ),
        duplicate_recall=(
            duplicate_tp / recall_denominator if recall_denominator else 0.0
        ),
        decisions=dict(decisions),
        errors=tuple(errors),
    )
    return assessments, report
