from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_serialization import (
    workflow_opened_from_record,
    workflow_opened_to_record,
)


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

    def _read_all(self) -> list[WorkflowOpened]:
        if not self._path.exists():
            return []

        events: list[WorkflowOpened] = []
        with open(self._path, "r", encoding="utf-8") as file:
            for line in file:
                line_str = line.strip()
                if not line_str:
                    continue
                record = json.loads(line_str)
                event = workflow_opened_from_record(record)
                events.append(event)
        return events

    def append_opened(self, event: WorkflowOpened) -> None:
        if not isinstance(event, WorkflowOpened):
            raise ValueError(
                f"Expected WorkflowOpened instance, got {type(event).__name__}"
            )

        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = workflow_opened_to_record(event)
        serialized_line = json.dumps(record) + "\n"

        with open(self._path, "a", encoding="utf-8") as file:
            file.write(serialized_line)

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
