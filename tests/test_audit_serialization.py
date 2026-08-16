import unittest
from datetime import datetime, timezone

from agent_lab.audit import AuditEvent, AuditEventType
from agent_lab.audit_serialization import (
    audit_event_from_record,
    audit_event_to_record,
)


class AuditSerializationTests(unittest.TestCase):
    def setUp(self):
        self.occurred_at = datetime(
            2026,
            8,
            16,
            10,
            30,
            tzinfo=timezone.utc,
        )
        self.metadata = {
            "system_recommendation": "REVIEW",
            "human_decision": "REQUEST_CORRECTION",
            "agrees_with_system": True,
            "correction_count": 1,
        }
        self.event = AuditEvent(
            event_id="event-001",
            event_type=AuditEventType.HUMAN_REVIEW_RECORDED,
            material_id="MAT-001",
            actor_id="specialist-001",
            occurred_at=self.occurred_at,
            review_id="review-001",
            metadata=self.metadata,
        )

    def test_serialization_contains_schema_version_one(self):
        record = audit_event_to_record(self.event)

        self.assertEqual(record["schema_version"], 1)

    def test_serialization_preserves_real_fields_and_types(self):
        record = audit_event_to_record(self.event)

        self.assertEqual(record["event_id"], "event-001")
        self.assertEqual(
            record["event_type"],
            AuditEventType.HUMAN_REVIEW_RECORDED.value,
        )
        self.assertEqual(record["material_id"], "MAT-001")
        self.assertEqual(record["actor_id"], "specialist-001")
        self.assertEqual(record["review_id"], "review-001")
        self.assertEqual(
            record["occurred_at"],
            "2026-08-16T10:30:00+00:00",
        )
        self.assertEqual(record["metadata"], self.metadata)

    def test_round_trip_preserves_valid_audit_event(self):
        record = audit_event_to_record(self.event)
        restored = audit_event_from_record(record)

        self.assertEqual(restored, self.event)
        self.assertEqual(restored.event_id, self.event.event_id)
        self.assertEqual(restored.event_type, self.event.event_type)
        self.assertEqual(restored.material_id, self.event.material_id)
        self.assertEqual(restored.actor_id, self.event.actor_id)
        self.assertEqual(restored.occurred_at, self.event.occurred_at)
        self.assertEqual(restored.review_id, self.event.review_id)
        self.assertEqual(restored.metadata, self.event.metadata)

    def test_deserialization_restores_enum_type(self):
        record = audit_event_to_record(self.event)
        restored = audit_event_from_record(record)

        self.assertIsInstance(restored.event_type, AuditEventType)
        self.assertEqual(
            restored.event_type,
            AuditEventType.HUMAN_REVIEW_RECORDED,
        )

    def test_deserialization_restores_frozen_metadata(self):
        record = audit_event_to_record(self.event)
        restored = audit_event_from_record(record)

        self.assertEqual(restored.metadata["agrees_with_system"], True)
        with self.assertRaises(TypeError):
            restored.metadata["agrees_with_system"] = False

    def test_deserialization_preserves_timezone_aware_datetime(self):
        record = audit_event_to_record(self.event)
        restored = audit_event_from_record(record)

        self.assertIsNotNone(restored.occurred_at.tzinfo)
        self.assertEqual(restored.occurred_at, self.occurred_at)

    def test_rejects_timestamp_without_timezone(self):
        record = audit_event_to_record(self.event)
        record["occurred_at"] = "2026-08-16T10:30:00"

        with self.assertRaises(ValueError):
            audit_event_from_record(record)

    def test_rejects_unknown_schema_version(self):
        record = audit_event_to_record(self.event)
        record["schema_version"] = 999

        with self.assertRaises(ValueError):
            audit_event_from_record(record)


if __name__ == "__main__":
    unittest.main()
