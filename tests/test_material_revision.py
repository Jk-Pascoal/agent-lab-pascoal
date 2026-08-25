from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, tzinfo
import unittest

import agent_lab.material_revision as material_revision_module
from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


class MaterialRevisionTests(unittest.TestCase):
    def test_creates_valid_root_revision(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        revision = MaterialRevision(
            revision_id="REV-001",
            record=record,
            revised_at=revised_at,
        )

        self.assertEqual(revision.revision_id, "REV-001")
        self.assertIs(revision.record, record)
        self.assertEqual(revision.revised_at, revised_at)
        self.assertIsNone(revision.predecessor_revision_id)
        self.assertIsNone(revision.source_review_id)
        self.assertEqual(revision.material_id, "MAT-001")

    def test_sanitizes_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        revision = MaterialRevision(
            revision_id="  REV-002  ",
            record=record,
            revised_at=revised_at,
        )

        self.assertEqual(revision.revision_id, "REV-002")

    def test_rejects_whitespace_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="   ",
                record=record,
                revised_at=revised_at,
            )

    def test_rejects_non_string_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id=123,  # type: ignore[arg-type]
                record=record,
                revised_at=revised_at,
            )

    def test_rejects_non_material_record(self) -> None:
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-003",
                record="not-a-material-record",  # type: ignore[arg-type]
                revised_at=revised_at,
            )

    def test_rejects_non_string_material_id(self) -> None:
        record = MaterialRecord(
            material_id=123,  # type: ignore[arg-type]
        )
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-004",
                record=record,
                revised_at=revised_at,
            )

    def test_rejects_whitespace_material_id(self) -> None:
        record = MaterialRecord(material_id="   ")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-005",
                record=record,
                revised_at=revised_at,
            )

    def test_preserves_material_id_without_normalization(self) -> None:
        record = MaterialRecord(material_id=" MAT-001 ")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        revision = MaterialRevision(
            revision_id="REV-006",
            record=record,
            revised_at=revised_at,
        )

        self.assertIs(revision.record, record)
        self.assertEqual(record.material_id, " MAT-001 ")
        self.assertEqual(revision.material_id, " MAT-001 ")

    def test_rejects_non_datetime_revised_at(self) -> None:
        record = MaterialRecord(material_id="MAT-001")

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-007",
                record=record,
                revised_at="2026-08-25T12:00:00Z",  # type: ignore[arg-type]
            )

    def test_rejects_naive_revised_at(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-008",
                record=record,
                revised_at=revised_at,
            )

    def test_sanitizes_predecessor_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        revision = MaterialRevision(
            revision_id="REV-010",
            record=record,
            revised_at=revised_at,
            predecessor_revision_id="  REV-009  ",
        )

        self.assertEqual(
            revision.predecessor_revision_id,
            "REV-009",
        )

    def test_rejects_whitespace_predecessor_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-010",
                record=record,
                revised_at=revised_at,
                predecessor_revision_id="   ",
            )

    def test_rejects_non_string_predecessor_revision_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-010",
                record=record,
                revised_at=revised_at,
                predecessor_revision_id=123,  # type: ignore[arg-type]
            )

    def test_sanitizes_source_review_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        revision = MaterialRevision(
            revision_id="REV-011",
            record=record,
            revised_at=revised_at,
            predecessor_revision_id="REV-010",
            source_review_id="  REVIEW-001  ",
        )

        self.assertEqual(
            revision.source_review_id,
            "REVIEW-001",
        )

    def test_rejects_whitespace_source_review_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-011",
                record=record,
                revised_at=revised_at,
                predecessor_revision_id="REV-010",
                source_review_id="   ",
            )

    def test_rejects_non_string_source_review_id(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-011",
                record=record,
                revised_at=revised_at,
                predecessor_revision_id="REV-010",
                source_review_id=123,  # type: ignore[arg-type]
            )

    def test_rejects_source_review_id_without_predecessor(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-012",
                record=record,
                revised_at=revised_at,
                source_review_id="REVIEW-001",
            )

    def test_rejects_self_referential_predecessor_after_sanitization(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="  REV-013  ",
                record=record,
                revised_at=revised_at,
                predecessor_revision_id="REV-013",
            )

    def test_creates_successor_revision_from_predecessor(self) -> None:
        predecessor_record = MaterialRecord(
            material_id="MAT-001",
            description_short="Before",
        )
        predecessor_revised_at = datetime(
            2026,
            8,
            25,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )
        predecessor = MaterialRevision(
            revision_id="REV-100",
            record=predecessor_record,
            revised_at=predecessor_revised_at,
        )

        successor_record = MaterialRecord(
            material_id="MAT-001",
            description_short="After",
        )
        successor_revised_at = datetime(
            2026,
            8,
            25,
            13,
            0,
            0,
            tzinfo=timezone.utc,
        )

        successor = material_revision_module.create_successor_revision(
            predecessor,
            revision_id="REV-101",
            record=successor_record,
            revised_at=successor_revised_at,
            source_review_id="REVIEW-001",
        )

        self.assertIsNot(successor, predecessor)
        self.assertEqual(successor.revision_id, "REV-101")
        self.assertIs(successor.record, successor_record)
        self.assertEqual(successor.material_id, "MAT-001")
        self.assertEqual(successor.revised_at, successor_revised_at)
        self.assertEqual(
            successor.predecessor_revision_id,
            "REV-100",
        )
        self.assertEqual(
            successor.source_review_id,
            "REVIEW-001",
        )

        self.assertEqual(predecessor.revision_id, "REV-100")
        self.assertIs(predecessor.record, predecessor_record)
        self.assertEqual(
            predecessor.revised_at,
            predecessor_revised_at,
        )
        self.assertIsNone(predecessor.predecessor_revision_id)
        self.assertIsNone(predecessor.source_review_id)

        self.assertEqual(
            successor_record.description_short,
            "After",
        )

    def test_rejects_non_material_revision_predecessor(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            13,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(TypeError):
            material_revision_module.create_successor_revision(
                "not-a-material-revision",  # type: ignore[arg-type]
                revision_id="REV-102",
                record=record,
                revised_at=revised_at,
            )

    def test_rejects_successor_with_different_exact_material_id(self) -> None:
        predecessor = MaterialRevision(
            revision_id="REV-200",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=datetime(
                2026,
                8,
                25,
                12,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

        successor_record = MaterialRecord(
            material_id=" MAT-001 ",
        )

        with self.assertRaises(ValueError):
            material_revision_module.create_successor_revision(
                predecessor,
                revision_id="REV-201",
                record=successor_record,
                revised_at=datetime(
                    2026,
                    8,
                    25,
                    13,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
            )

    def test_rejects_successor_revised_before_predecessor(self) -> None:
        predecessor = MaterialRevision(
            revision_id="REV-300",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=datetime(
                2026,
                8,
                25,
                13,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            material_revision_module.create_successor_revision(
                predecessor,
                revision_id="REV-301",
                record=MaterialRecord(material_id="MAT-001"),
                revised_at=datetime(
                    2026,
                    8,
                    25,
                    12,
                    59,
                    59,
                    tzinfo=timezone.utc,
                ),
            )

    def test_allows_successor_with_equal_revised_at(self) -> None:
        revised_at = datetime(
            2026,
            8,
            25,
            13,
            0,
            0,
            tzinfo=timezone.utc,
        )

        predecessor = MaterialRevision(
            revision_id="REV-310",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=revised_at,
        )

        successor = material_revision_module.create_successor_revision(
            predecessor,
            revision_id="REV-311",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=revised_at,
        )

        self.assertEqual(successor.revised_at, revised_at)
        self.assertEqual(
            successor.predecessor_revision_id,
            "REV-310",
        )

    def test_rejects_non_material_record_in_create_successor_revision(self) -> None:
        predecessor = MaterialRevision(
            revision_id="REV-400",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=datetime(
                2026,
                8,
                25,
                13,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            material_revision_module.create_successor_revision(
                predecessor,
                revision_id="REV-401",
                record="not-a-material-record",  # type: ignore[arg-type]
                revised_at=datetime(
                    2026,
                    8,
                    25,
                    14,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
            )

    def test_rejects_successor_with_identical_revision_id(self) -> None:
        predecessor = MaterialRevision(
            revision_id="REV-410",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=datetime(
                2026,
                8,
                25,
                13,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            material_revision_module.create_successor_revision(
                predecessor,
                revision_id="REV-410",
                record=MaterialRecord(material_id="MAT-001"),
                revised_at=datetime(
                    2026,
                    8,
                    25,
                    14,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
            )

    def test_rejects_revised_at_with_tzinfo_but_no_utc_offset(self) -> None:
        record = MaterialRecord(material_id="MAT-001")
        revised_at = datetime(
            2026,
            8,
            25,
            13,
            0,
            0,
            tzinfo=_NoneOffsetTimezone(),
        )

        with self.assertRaises(ValueError):
            MaterialRevision(
                revision_id="REV-420",
                record=record,
                revised_at=revised_at,
            )

    def test_material_revision_is_strictly_immutable(self) -> None:
        revision = MaterialRevision(
            revision_id="REV-430",
            record=MaterialRecord(material_id="MAT-001"),
            revised_at=datetime(
                2026,
                8,
                25,
                13,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(FrozenInstanceError):
            revision.revision_id = "REV-431"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
