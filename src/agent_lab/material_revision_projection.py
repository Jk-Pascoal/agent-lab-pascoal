from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from agent_lab.material_revision import MaterialRevision


@dataclass(frozen=True, slots=True)
class MaterialRevisionLineage:
    material_id: str
    revisions: tuple[MaterialRevision, ...]
    root_revision_ids: tuple[str, ...]
    head_revision_ids: tuple[str, ...]
    orphan_revision_ids: tuple[str, ...]
    fork_predecessor_ids: tuple[str, ...]
    cycle_revision_ids: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return len(self.revisions) == 0

    @property
    def is_linear(self) -> bool:
        return (
            len(self.root_revision_ids) == 1
            and len(self.head_revision_ids) == 1
            and not self.has_orphans
            and not self.has_forks
            and not self.has_cycles
        )

    @property
    def has_orphans(self) -> bool:
        return len(self.orphan_revision_ids) > 0

    @property
    def has_forks(self) -> bool:
        return len(self.fork_predecessor_ids) > 0

    @property
    def has_multiple_roots(self) -> bool:
        return len(self.root_revision_ids) > 1

    @property
    def has_cycles(self) -> bool:
        return len(self.cycle_revision_ids) > 0

    @property
    def has_ambiguities(self) -> bool:
        return (
            self.has_orphans
            or self.has_forks
            or self.has_multiple_roots
            or self.has_cycles
            or len(self.head_revision_ids) != 1
        )


def project_material_revision_lineage(
    revisions: Sequence[MaterialRevision],
) -> MaterialRevisionLineage:
    canonical_revisions = tuple(sorted(revisions, key=lambda r: r.revision_id))
    material_id = canonical_revisions[0].material_id

    revision_ids = {
        revision.revision_id for revision in canonical_revisions
    }

    root_revision_ids = tuple(
        sorted(
            r.revision_id
            for r in canonical_revisions
            if r.predecessor_revision_id is None
        )
    )

    orphan_revision_ids = tuple(
        sorted(
            r.revision_id
            for r in canonical_revisions
            if r.predecessor_revision_id is not None
            and r.predecessor_revision_id not in revision_ids
        )
    )

    referenced_preds = {
        r.predecessor_revision_id
        for r in canonical_revisions
        if r.predecessor_revision_id is not None
    }

    head_revision_ids = tuple(
        sorted(
            r.revision_id
            for r in canonical_revisions
            if r.revision_id not in referenced_preds
        )
    )

    return MaterialRevisionLineage(
        material_id=material_id,
        revisions=canonical_revisions,
        root_revision_ids=root_revision_ids,
        head_revision_ids=head_revision_ids,
        orphan_revision_ids=orphan_revision_ids,
        fork_predecessor_ids=(),
        cycle_revision_ids=(),
    )
