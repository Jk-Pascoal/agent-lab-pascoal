from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from agent_lab.material_revision import MaterialRevision
from agent_lab.material_revision_serialization import (
    material_revision_from_record,
    material_revision_to_record,
)


class MaterialRevisionPersistenceError(Exception):
    """Base error for material revision persistence operations."""


class DuplicateMaterialRevisionError(MaterialRevisionPersistenceError):
    """Raised when attempting to append a MaterialRevision with an existing revision_id."""


@runtime_checkable
class MaterialRevisionRepository(Protocol):
    """Abstract protocol for append-only material revision persistence."""

    def append(self, revision: MaterialRevision) -> None: ...

    def get_by_id(self, revision_id: str) -> MaterialRevision | None: ...

    def list_by_material(
        self, material_id: str
    ) -> tuple[MaterialRevision, ...]: ...

    def list_all(self) -> tuple[MaterialRevision, ...]: ...


class JsonlMaterialRevisionRepository:
    """Append-only local JSONL file repository for MaterialRevisions."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def _read_all(self) -> list[MaterialRevision]:
        if not self._path.exists():
            return []

        with open(self._path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        revisions: list[MaterialRevision] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            revision = material_revision_from_record(record)
            revisions.append(revision)

        return revisions

    def append(self, revision: MaterialRevision) -> None:
        if self.get_by_id(revision.revision_id) is not None:
            raise DuplicateMaterialRevisionError(
                f"MaterialRevision with revision_id '{revision.revision_id}' already exists in {self._path}"
            )

        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = material_revision_to_record(revision)
        line = json.dumps(record)

        with open(self._path, "a", encoding="utf-8") as file:
            file.write(f"{line}\n")
            file.flush()
            os.fsync(file.fileno())

    def get_by_id(self, revision_id: str) -> MaterialRevision | None:
        for rev in self._read_all():
            if rev.revision_id == revision_id:
                return rev
        return None

    def list_by_material(
        self, material_id: str
    ) -> tuple[MaterialRevision, ...]:
        return tuple(
            rev for rev in self._read_all() if rev.record.material_id == material_id
        )

    def list_all(self) -> tuple[MaterialRevision, ...]:
        return tuple(self._read_all())
