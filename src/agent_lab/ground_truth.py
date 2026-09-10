from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .domain import GovernanceDecision, IssueType
from .human_review import VerifiedSpecialistIdentity


class LabelProvenance(StrEnum):
    SPECIALIST_CURATED = "SPECIALIST_CURATED"
    SYNTHETIC_SPECIFIED = "SYNTHETIC_SPECIFIED"


def _normalize_required_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a str"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty or whitespace"
        )

    return normalized


def _validate_provenance_annotator(
    provenance: object,
    annotator: object,
) -> None:
    if not isinstance(provenance, LabelProvenance):
        raise TypeError(
            "provenance must be a LabelProvenance"
        )

    if provenance == LabelProvenance.SPECIALIST_CURATED:
        if annotator is None:
            raise ValueError(
                "annotator is required for SPECIALIST_CURATED"
            )
        if not isinstance(
            annotator,
            VerifiedSpecialistIdentity,
        ):
            raise TypeError(
                "annotator must be a VerifiedSpecialistIdentity"
            )
    elif provenance == LabelProvenance.SYNTHETIC_SPECIFIED:
        if annotator is not None:
            raise ValueError(
                "annotator must be None for SYNTHETIC_SPECIFIED"
            )


def _validate_label_temporal_consistency(
    provenance: LabelProvenance,
    annotator: VerifiedSpecialistIdentity | None,
    labeled_at: object,
) -> None:
    if not isinstance(labeled_at, datetime):
        raise TypeError(
            "labeled_at must be a datetime"
        )

    if (
        labeled_at.tzinfo is None
        or labeled_at.utcoffset() is None
    ):
        raise ValueError(
            "labeled_at must be timezone-aware"
        )

    if (
        provenance == LabelProvenance.SPECIALIST_CURATED
        and annotator is not None
        and annotator.verified_at > labeled_at
    ):
        raise ValueError(
            "annotator.verified_at cannot be after labeled_at"
        )


@dataclass(frozen=True, slots=True)
class MaterialRuleGroundTruth:
    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_issue_types: tuple[IssueType, ...]
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id",
            "source_reference",
            "rationale",
        )
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(self.expected_issue_types, tuple):
            raise TypeError("expected_issue_types must be a tuple")

        for item in self.expected_issue_types:
            if not isinstance(item, IssueType):
                raise TypeError(
                    "expected_issue_types must contain only IssueType instances"
                )

        if IssueType.POSSIBLE_DUPLICATE in self.expected_issue_types:
            raise ValueError(
                "POSSIBLE_DUPLICATE is not permitted in MaterialRuleGroundTruth"
            )

        if len(self.expected_issue_types) != len(set(self.expected_issue_types)):
            raise ValueError("expected_issue_types must not contain duplicates")

        canonical = tuple(
            sorted(self.expected_issue_types, key=lambda item: item.value)
        )
        object.__setattr__(self, "expected_issue_types", canonical)

        _validate_provenance_annotator(
            self.provenance,
            self.annotator,
        )

        _validate_label_temporal_consistency(
            self.provenance,
            self.annotator,
            self.labeled_at,
        )


@dataclass(frozen=True, slots=True)
class DuplicatePairGroundTruth:
    evaluation_case_id: str
    ground_truth_id: str
    material_id_a: str
    material_id_b: str
    is_duplicate: bool
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id_a",
            "material_id_b",
            "source_reference",
            "rationale",
        )
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(self.is_duplicate, bool):
            raise TypeError("is_duplicate must be a bool")

        if self.material_id_a == self.material_id_b:
            raise ValueError(
                "material_id_a and material_id_b must be different"
            )

        if self.material_id_a > self.material_id_b:
            raise ValueError(
                "material_id_a must be less than material_id_b"
            )

        _validate_provenance_annotator(
            self.provenance,
            self.annotator,
        )

        _validate_label_temporal_consistency(
            self.provenance,
            self.annotator,
            self.labeled_at,
        )


@dataclass(frozen=True, slots=True)
class DecisionRecommendationGroundTruth:
    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_recommendation: GovernanceDecision
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        text_fields = (
            "evaluation_case_id",
            "ground_truth_id",
            "material_id",
            "source_reference",
            "rationale",
        )

        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(
            self.expected_recommendation,
            GovernanceDecision,
        ):
            raise TypeError(
                "expected_recommendation must be a GovernanceDecision"
            )

        _validate_provenance_annotator(
            self.provenance,
            self.annotator,
        )

        _validate_label_temporal_consistency(
            self.provenance,
            self.annotator,
            self.labeled_at,
        )
