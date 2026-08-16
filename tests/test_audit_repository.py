from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from agent_lab.audit import AuditEvent, AuditEventType
from agent_lab.audit_repository import (
    AuditCorruptionError,
    AuditPersistenceError,
    AuditRepository,
    DuplicateAuditEventError,
    JsonlAuditRepository,
)
from agent_lab.audit_serialization import audit_event_to_record


class JsonlAuditRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "audit_events.jsonl"
        self.repository = JsonlAuditRepository(self.file_path)
        self.occurred_at = datetime(
            2026,
            8,
            16,
            11,
            0,
            tzinfo=timezone.utc,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def build_event(
        self,
        *,
        event_id: str = "event-001",
        material_id: str = "MAT-001",
        actor_id: str = "specialist-001",
        review_id: str = "review-001",
        occurred_at: datetime | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        return AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.HUMAN_REVIEW_RECORDED,
            material_id=material_id,
            actor_id=actor_id,
            occurred_at=occurred_at or self.occurred_at,
            review_id=review_id,
            metadata=metadata
            if metadata is not None
            else {
                "system_recommendation": "REVIEW",
                "human_decision": "REQUEST_CORRECTION",
                "agrees_with_system": True,
            },
        )

    def test_nonexistent_file_returns_empty_collection(self) -> None:
        self.assertEqual(self.repository.list_all(), ())

    def test_empty_file_returns_empty_collection(self) -> None:
        self.file_path.touch()

        self.assertEqual(self.repository.list_all(), ())

    def test_append_persists_event_as_single_json_line(self) -> None:
        event = self.build_event()
        self.repository.append(event)

        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)

        record = json.loads(lines[0])
        self.assertEqual(record["event_id"], "event-001")
        self.assertEqual(record["material_id"], "MAT-001")

    def test_new_repository_instance_recovers_persisted_event(self) -> None:
        event = self.build_event()
        self.repository.append(event)

        reopened = JsonlAuditRepository(self.file_path)
        self.assertEqual(reopened.list_all(), (event,))

    def test_get_by_id_returns_existing_event(self) -> None:
        event = self.build_event()
        self.repository.append(event)

        retrieved = self.repository.get_by_id("event-001")
        self.assertEqual(retrieved, event)

    def test_get_by_id_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self.repository.get_by_id("non-existent-event"))

    def test_list_by_material_filters_and_preserves_recording_order(
        self,
    ) -> None:
        event1 = self.build_event(
            event_id="event-001",
            material_id="MAT-001",
            occurred_at=datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc),
        )
        event2 = self.build_event(
            event_id="event-002",
            material_id="MAT-002",
            occurred_at=datetime(2026, 8, 16, 11, 0, tzinfo=timezone.utc),
        )
        event3 = self.build_event(
            event_id="event-003",
            material_id="MAT-001",
            occurred_at=datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc),
        )

        self.repository.append(event1)
        self.repository.append(event2)
        self.repository.append(event3)

        results = self.repository.list_by_material("MAT-001")
        self.assertEqual(results, (event1, event3))

    def test_list_all_preserves_recording_order(self) -> None:
        event_late = self.build_event(
            event_id="event-001",
            material_id="MAT-001",
            occurred_at=datetime(2026, 8, 16, 14, 0, tzinfo=timezone.utc),
        )
        event_early = self.build_event(
            event_id="event-002",
            material_id="MAT-002",
            occurred_at=datetime(2026, 8, 16, 8, 0, tzinfo=timezone.utc),
        )

        self.repository.append(event_late)
        self.repository.append(event_early)

        self.assertEqual(self.repository.list_all(), (event_late, event_early))

    def test_rejects_duplicate_event_id(self) -> None:
        event1 = self.build_event(event_id="event-001")
        duplicate_id_event = self.build_event(
            event_id="event-001",
            material_id="MAT-002",
        )

        self.repository.append(event1)

        with self.assertRaises(DuplicateAuditEventError):
            self.repository.append(duplicate_id_event)

    def test_malformed_json_raises_corruption_error(self) -> None:
        self.file_path.write_text("INVALID JSON LINE\n", encoding="utf-8")

        with self.assertRaises(AuditCorruptionError):
            self.repository.list_all()

    def test_corruption_error_exposes_line_number(self) -> None:
        valid_record = json.dumps(audit_event_to_record(self.build_event()))
        corrupted_content = f"{valid_record}\nMALFORMED JSON\n"
        self.file_path.write_text(corrupted_content, encoding="utf-8")

        with self.assertRaises(AuditCorruptionError) as context:
            self.repository.list_all()

        self.assertEqual(context.exception.line_number, 2)

    def test_corruption_after_valid_event_does_not_return_partial_history(
        self,
    ) -> None:
        valid_record = json.dumps(audit_event_to_record(self.build_event()))
        corrupted_content = f"{valid_record}\nMALFORMED JSON\n"
        self.file_path.write_text(corrupted_content, encoding="utf-8")

        with self.assertRaises(AuditCorruptionError):
            self.repository.list_all()

        with self.assertRaises(AuditCorruptionError):
            self.repository.get_by_id("event-001")

        with self.assertRaises(AuditCorruptionError):
            self.repository.list_by_material("MAT-001")

    def test_persisted_record_contains_schema_version_one(self) -> None:
        event = self.build_event()
        self.repository.append(event)

        line = self.file_path.read_text(encoding="utf-8").strip()
        record = json.loads(line)

        self.assertEqual(record["schema_version"], 1)

    def test_public_api_does_not_expose_update_or_delete(self) -> None:
        forbidden_methods = ("update", "delete", "remove", "pop", "clear")

        for method_name in forbidden_methods:
            with self.subTest(
                target="JsonlAuditRepository", method=method_name
            ):
                self.assertFalse(hasattr(self.repository, method_name))
            with self.subTest(target="AuditRepository", method=method_name):
                self.assertFalse(hasattr(AuditRepository, method_name))

    def test_exceptions_inherit_from_audit_persistence_error(self) -> None:
        self.assertTrue(
            issubclass(DuplicateAuditEventError, AuditPersistenceError)
        )
        self.assertTrue(issubclass(AuditCorruptionError, AuditPersistenceError))
        self.assertTrue(issubclass(AuditPersistenceError, Exception))

    @patch("agent_lab.audit_repository.os.fsync")
    def test_append_calls_fsync(self, mock_fsync) -> None:
        event = self.build_event()
        self.repository.append(event)

        mock_fsync.assert_called_once()
        file_descriptor = mock_fsync.call_args[0][0]
        self.assertIsInstance(file_descriptor, int)

    @patch(
        "agent_lab.audit_repository.os.fsync",
        side_effect=OSError("simulated fsync failure"),
    )
    def test_fsync_failure_is_reported_as_persistence_error(
        self, _mock_fsync
    ) -> None:
        event = self.build_event()

        with self.assertRaises(AuditPersistenceError) as context:
            self.repository.append(event)

        self.assertIsNotNone(context.exception.__cause__)
        self.assertIsInstance(context.exception.__cause__, OSError)
        self.assertEqual(
            str(context.exception.__cause__),
            "simulated fsync failure",
        )


if __name__ == "__main__":
    unittest.main()
