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
