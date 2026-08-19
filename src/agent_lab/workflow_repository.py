from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_serialization import (
    workflow_opened_from_record,
    workflow_opened_to_record,
)


class WorkflowPersistenceError(Exception):
    """Base error for workflow lifecycle persistence."""


class DuplicateWorkflowEventError(WorkflowPersistenceError):
    """Raised when event_id already exists."""


class WorkflowAlreadyOpenedError(WorkflowPersistenceError):
    """Raised when a second WorkflowOpened uses the same workflow_id."""


class WorkflowCorruptionError(WorkflowPersistenceError):
    """Raised when persisted lifecycle history is corrupted."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


class WorkflowLifecycleRepository(Protocol):
    """Protocol defining the repository contract for workflow lifecycle events."""

    def append_opened(self, event: WorkflowOpened) -> None: ...
    def get_opened_by_id(self, event_id: str) -> WorkflowOpened | None: ...
    def get_opened_by_workflow_id(
        self, workflow_id: str
    ) -> WorkflowOpened | None: ...
    def list_opened_by_material(
        self, material_id: str
    ) -> tuple[WorkflowOpened, ...]: ...
    def list_all_opened(self) -> tuple[WorkflowOpened, ...]: ...


class JsonlWorkflowLifecycleRepository:
    """Append-only JSONL implementation of WorkflowLifecycleRepository."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def _read_all(self) -> list[WorkflowOpened]:
        if not self._path.exists():
            return []

        try:
            with open(self._path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except OSError as exc:
            raise WorkflowPersistenceError(
                f"Failed to read workflow file: {self._path}"
            ) from exc

        events: list[WorkflowOpened] = []
        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                raise WorkflowCorruptionError(
                    f"Empty line detected at line {line_idx} in {self._path}",
                    line_number=line_idx,
                )

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise WorkflowCorruptionError(
                    f"Malformed JSON at line {line_idx} in {self._path}: {exc}",
                    line_number=line_idx,
                ) from exc

            if not isinstance(record, dict):
                raise WorkflowCorruptionError(
                    f"Record at line {line_idx} is not a JSON object: {record!r}",
                    line_number=line_idx,
                )

            try:
                event = workflow_opened_from_record(record)
            except ValueError as exc:
                raise WorkflowCorruptionError(
                    f"Invalid workflow record at line {line_idx}: {exc}",
                    line_number=line_idx,
                ) from exc

            events.append(event)

        return events

    def append_opened(self, event: WorkflowOpened) -> None:
        if not isinstance(event, WorkflowOpened):
            raise ValueError(
                f"Expected WorkflowOpened instance, got {type(event).__name__}"
            )

        existing_events = self._read_all()
        for existing in existing_events:
            if existing.event_id == event.event_id:
                raise DuplicateWorkflowEventError(
                    f"WorkflowOpened event with event_id '{event.event_id}' already exists in {self._path}"
                )
            if existing.workflow_id == event.workflow_id:
                raise WorkflowAlreadyOpenedError(
                    f"Workflow with workflow_id '{event.workflow_id}' has already been opened in {self._path}"
                )

        record = workflow_opened_to_record(event)
        try:
            line = json.dumps(record, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise WorkflowPersistenceError(
                f"Failed to serialize workflow event {event.event_id} to JSON"
            ) from exc

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as file:
                file.write(f"{line}\n")
                file.flush()
                os.fsync(file.fileno())
        except OSError as exc:
            raise WorkflowPersistenceError(
                f"Failed to append workflow event to file {self._path}"
            ) from exc

    def get_opened_by_id(self, event_id: str) -> WorkflowOpened | None:
        if not isinstance(event_id, str):
            raise ValueError(
                f"event_id must be a string, got {type(event_id).__name__}"
            )

        for event in self._read_all():
            if event.event_id == event_id:
                return event
        return None

    def get_opened_by_workflow_id(
        self, workflow_id: str
    ) -> WorkflowOpened | None:
        if not isinstance(workflow_id, str):
            raise ValueError(
                f"workflow_id must be a string, got {type(workflow_id).__name__}"
            )

        for event in self._read_all():
            if event.workflow_id == workflow_id:
                return event
        return None

    def list_opened_by_material(
        self, material_id: str
    ) -> tuple[WorkflowOpened, ...]:
        if not isinstance(material_id, str):
            raise ValueError(
                f"material_id must be a string, got {type(material_id).__name__}"
            )

        return tuple(
            event
            for event in self._read_all()
            if event.recommendation.material_id == material_id
        )

    def list_all_opened(self) -> tuple[WorkflowOpened, ...]:
        return tuple(self._read_all())
