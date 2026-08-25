from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.domain import MaterialRecord


def _require_non_blank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value.strip()


@dataclass(frozen=True, slots=True)
class MaterialRevision:
    revision_id: str
    record: MaterialRecord
    revised_at: datetime
    predecessor_revision_id: str | None = None
    source_review_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "revision_id",
            _require_non_blank(self.revision_id, "revision_id"),
        )

        if not isinstance(self.record, MaterialRecord):
            raise ValueError("record must be a MaterialRecord")

        _require_non_blank(
            self.record.material_id,
            "record.material_id",
        )

        if not isinstance(self.revised_at, datetime):
            raise ValueError("revised_at must be a datetime")

        if (
            self.revised_at.tzinfo is None
            or self.revised_at.utcoffset() is None
        ):
            raise ValueError("revised_at must be timezone-aware")

        if self.predecessor_revision_id is not None:
            object.__setattr__(
                self,
                "predecessor_revision_id",
                _require_non_blank(
                    self.predecessor_revision_id,
                    "predecessor_revision_id",
                ),
            )

        if (
            self.predecessor_revision_id is not None
            and self.predecessor_revision_id == self.revision_id
        ):
            raise ValueError(
                "predecessor_revision_id must differ from revision_id"
            )

        if self.source_review_id is not None:
            object.__setattr__(
                self,
                "source_review_id",
                _require_non_blank(
                    self.source_review_id,
                    "source_review_id",
                ),
            )

        if (
            self.source_review_id is not None
            and self.predecessor_revision_id is None
        ):
            raise ValueError(
                "source_review_id requires predecessor_revision_id"
            )

    @property
    def material_id(self) -> str:
        return self.record.material_id


def create_successor_revision(
    predecessor: MaterialRevision,
    *,
    revision_id: str,
    record: MaterialRecord,
    revised_at: datetime,
    source_review_id: str | None = None,
) -> MaterialRevision:
    if not isinstance(predecessor, MaterialRevision):
        raise TypeError("predecessor must be a MaterialRevision")

    successor = MaterialRevision(
        revision_id=revision_id,
        record=record,
        revised_at=revised_at,
        predecessor_revision_id=predecessor.revision_id,
        source_review_id=source_review_id,
    )

    if successor.material_id != predecessor.material_id:
        raise ValueError(
            "record.material_id must match predecessor.material_id"
        )

    if successor.revised_at < predecessor.revised_at:
        raise ValueError(
            "revised_at must not be before predecessor.revised_at"
        )

    return successor




