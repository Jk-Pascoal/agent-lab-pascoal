from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .domain import IssueType
from .human_review import VerifiedSpecialistIdentity


class LabelProvenance(StrEnum):
    SPECIALIST_CURATED = "SPECIALIST_CURATED"
    SYNTHETIC_SPECIFIED = "SYNTHETIC_SPECIFIED"


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
            val = getattr(self, field_name)
            if not isinstance(val, str):
                raise TypeError(f"{field_name} must be a str")
            normalized = val.strip()
            if not normalized:
                raise ValueError(f"{field_name} must not be empty or whitespace")
            object.__setattr__(self, field_name, normalized)

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

        if not isinstance(self.provenance, LabelProvenance):
            raise TypeError("provenance must be a LabelProvenance")

        if self.provenance == LabelProvenance.SPECIALIST_CURATED:
            if self.annotator is None:
                raise ValueError("annotator is required for SPECIALIST_CURATED")
            if not isinstance(self.annotator, VerifiedSpecialistIdentity):
                raise TypeError(
                    "annotator must be a VerifiedSpecialistIdentity"
                )
        elif self.provenance == LabelProvenance.SYNTHETIC_SPECIFIED:
            if self.annotator is not None:
                raise ValueError(
                    "annotator must be None for SYNTHETIC_SPECIFIED"
                )

        if not isinstance(self.labeled_at, datetime):
            raise TypeError("labeled_at must be a datetime")

        if self.labeled_at.tzinfo is None or self.labeled_at.utcoffset() is None:
            raise ValueError("labeled_at must be timezone-aware")

        if (
            self.provenance == LabelProvenance.SPECIALIST_CURATED
            and self.annotator is not None
            and self.annotator.verified_at > self.labeled_at
        ):
            raise ValueError(
                "annotator.verified_at cannot be after labeled_at"
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
            val = getattr(self, field_name)
            if not isinstance(val, str):
                raise TypeError(f"{field_name} must be a str")
            normalized = val.strip()
            if not normalized:
                raise ValueError(f"{field_name} must not be empty or whitespace")
            object.__setattr__(self, field_name, normalized)

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

        if not isinstance(self.provenance, LabelProvenance):
            raise TypeError("provenance must be a LabelProvenance")

        if self.provenance == LabelProvenance.SPECIALIST_CURATED:
            if self.annotator is None:
                raise ValueError("annotator is required for SPECIALIST_CURATED")
            if not isinstance(self.annotator, VerifiedSpecialistIdentity):
                raise TypeError(
                    "annotator must be a VerifiedSpecialistIdentity"
                )
        elif self.provenance == LabelProvenance.SYNTHETIC_SPECIFIED:
            if self.annotator is not None:
                raise ValueError(
                    "annotator must be None for SYNTHETIC_SPECIFIED"
                )

        if not isinstance(self.labeled_at, datetime):
            raise TypeError("labeled_at must be a datetime")

        if (
            self.labeled_at.tzinfo is None
            or self.labeled_at.utcoffset() is None
        ):
            raise ValueError("labeled_at must be timezone-aware")

        if (
            self.provenance == LabelProvenance.SPECIALIST_CURATED
            and self.annotator is not None
            and self.annotator.verified_at > self.labeled_at
        ):
            raise ValueError(
                "annotator.verified_at cannot be after labeled_at"
            )
