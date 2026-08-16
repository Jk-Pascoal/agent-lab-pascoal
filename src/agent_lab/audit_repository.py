from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from agent_lab.audit import AuditEvent
from agent_lab.audit_serialization import (
    audit_event_from_record,
    audit_event_to_record,
)


class AuditPersistenceError(Exception):
    """Base error for audit persistence operations."""


class DuplicateAuditEventError(AuditPersistenceError):
    """Raised when attempting to append an AuditEvent with an existing event_id."""


class AuditCorruptionError(AuditPersistenceError):
    """Raised when an audit record or file is corrupted or structurally invalid."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


class AuditRepository(Protocol):
    """Abstract protocol for append-only audit event persistence."""

    def append(self, event: AuditEvent) -> None: ...

    def get_by_id(self, event_id: str) -> AuditEvent | None: ...

    def list_by_material(self, material_id: str) -> tuple[AuditEvent, ...]: ...

    def list_all(self) -> tuple[AuditEvent, ...]: ...


class JsonlAuditRepository:
    """Append-only local JSONL file repository for AuditEvents."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def _read_all_events(self) -> list[AuditEvent]:
        if not self._path.exists():
            return []

        try:
            with self._path.open("r", encoding="utf-8") as file:
                lines = file.readlines()
        except OSError as exc:
            raise AuditPersistenceError(
                f"Failed to read audit file: {self._path}"
            ) from exc

        events: list[AuditEvent] = []
        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                raise AuditCorruptionError(
                    f"Empty line detected at line {line_idx} in {self._path}",
                    line_number=line_idx,
                )

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditCorruptionError(
                    f"Malformed JSON at line {line_idx} in {self._path}: {exc}",
                    line_number=line_idx,
                ) from exc

            if not isinstance(record, dict):
                raise AuditCorruptionError(
                    f"Record at line {line_idx} is not a JSON object: {record!r}",
                    line_number=line_idx,
                )

            try:
                event = audit_event_from_record(record)
            except ValueError as exc:
                raise AuditCorruptionError(
                    f"Invalid audit record at line {line_idx}: {exc}",
                    line_number=line_idx,
                ) from exc

            events.append(event)

        return events

    def append(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise ValueError("event must be an AuditEvent instance")

        existing_events = self._read_all_events()
        for existing in existing_events:
            if existing.event_id == event.event_id:
                raise DuplicateAuditEventError(
                    f"AuditEvent with event_id '{event.event_id}' already exists in {self._path}"
                )

        record = audit_event_to_record(event)
        try:
            line = json.dumps(record, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise AuditPersistenceError(
                f"Failed to serialize audit event {event.event_id} to JSON"
            ) from exc

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as file:
                file.write(f"{line}\n")
                file.flush()
                os.fsync(file.fileno())
        except OSError as exc:
            raise AuditPersistenceError(
                f"Failed to append audit event to file {self._path}"
            ) from exc

    def get_by_id(self, event_id: str) -> AuditEvent | None:
        if not isinstance(event_id, str):
            raise ValueError("event_id must be a string")

        events = self._read_all_events()
        for event in events:
            if event.event_id == event_id:
                return event
        return None

    def list_by_material(self, material_id: str) -> tuple[AuditEvent, ...]:
        if not isinstance(material_id, str):
            raise ValueError("material_id must be a string")

        events = self._read_all_events()
        return tuple(
            event for event in events if event.material_id == material_id
        )

    def list_all(self) -> tuple[AuditEvent, ...]:
        return tuple(self._read_all_events())
