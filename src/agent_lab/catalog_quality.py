"""Read-model de domínio para diagnóstico de qualidade de catálogo (Slice 1A)."""

from dataclasses import dataclass

from .domain import GovernanceAssessment


@dataclass(frozen=True, slots=True)
class CatalogQualityReport:
    """Read-model imutável de diagnóstico de catálogo."""

    catalog_id: str
    assessments: tuple[GovernanceAssessment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.catalog_id, str) or isinstance(self.catalog_id, bool):
            raise TypeError("catalog_id must be a str")

        normalized_id = self.catalog_id.strip()
        if not normalized_id:
            raise ValueError("catalog_id must not be empty or whitespace")
        object.__setattr__(self, "catalog_id", normalized_id)

        if not isinstance(self.assessments, tuple):
            raise TypeError("assessments must be a tuple")

        for item in self.assessments:
            if not isinstance(item, GovernanceAssessment):
                raise TypeError("all items in assessments must be GovernanceAssessment instances")

            material_id = item.material_id
            if not isinstance(material_id, str) or isinstance(material_id, bool):
                raise TypeError("assessment.material_id must be a str")

            if not material_id.strip():
                raise ValueError("assessment.material_id must not be empty or whitespace")

            if material_id != material_id.strip():
                raise ValueError("assessment.material_id must not contain outer whitespace")

        material_ids = [a.material_id for a in self.assessments]
        if material_ids != sorted(material_ids):
            raise ValueError("assessments must be sorted in ascending order by material_id")

        if len(material_ids) != len(set(material_ids)):
            raise ValueError("assessments must contain unique material_ids")

        # Pass 1: Validação estrutural de duplicate_candidates em todos os assessments
        for assessment in self.assessments:
            candidates = assessment.duplicate_candidates
            if not isinstance(candidates, tuple):
                raise TypeError("duplicate_candidates must be a tuple")

            for candidate_id in candidates:
                if not isinstance(candidate_id, str) or isinstance(candidate_id, bool):
                    raise TypeError("duplicate_candidates elements must be str")

        # Pass 2: Invariantes locais de duplicate_candidates
        assessment_by_id = {
            assessment.material_id: assessment
            for assessment in self.assessments
        }

        for assessment in self.assessments:
            candidates = assessment.duplicate_candidates

            for candidate_id in candidates:
                if candidate_id == assessment.material_id:
                    raise ValueError(
                        f"self-referential duplicate candidate in assessment {assessment.material_id!r}"
                    )
                if candidate_id not in assessment_by_id:
                    raise ValueError(
                        f"orphan duplicate candidate {candidate_id!r} in assessment {assessment.material_id!r}"
                    )

            if len(candidates) != len(set(candidates)):
                raise ValueError(
                    f"duplicate entries in duplicate_candidates for assessment {assessment.material_id!r}"
                )

            if list(candidates) != sorted(candidates):
                raise ValueError(
                    f"duplicate_candidates not sorted in assessment {assessment.material_id!r}"
                )

        # Pass 3: Simetria relacional global (A -> B <=> B -> A)
        for assessment in self.assessments:
            for candidate_id in assessment.duplicate_candidates:
                other_assessment = assessment_by_id[candidate_id]
                if assessment.material_id not in other_assessment.duplicate_candidates:
                    raise ValueError(
                        f"asymmetric duplicate relation between {assessment.material_id!r} and {candidate_id!r}"
                    )

    @property
    def total_records(self) -> int:
        return len(self.assessments)

    @property
    def is_empty(self) -> bool:
        return self.total_records == 0

    @property
    def clean_records_count(self) -> int:
        return sum(1 for a in self.assessments if len(a.issues) == 0)

    @property
    def duplicate_pairs(self) -> tuple[tuple[str, str], ...]:
        pairs: set[tuple[str, str]] = set()
        for assessment in self.assessments:
            m_id = assessment.material_id
            for candidate_id in assessment.duplicate_candidates:
                if m_id < candidate_id:
                    pairs.add((m_id, candidate_id))
        return tuple(sorted(pairs))

    @property
    def duplicate_pairs_count(self) -> int:
        return len(self.duplicate_pairs)

    @property
    def clean_records_ratio(self) -> float | None:
        if self.is_empty:
            return None
        return self.clean_records_count / self.total_records

    @property
    def average_completeness(self) -> float | None:
        if self.is_empty:
            return None
        return sum(a.completeness for a in self.assessments) / self.total_records
