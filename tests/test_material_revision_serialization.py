from datetime import datetime, timedelta, timezone
import unittest

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision
from agent_lab.material_revision_serialization import (
    SCHEMA_VERSION_V1,
    material_revision_from_record,
    material_revision_to_record,
)


class MaterialRevisionSerializationRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.revised_at = datetime(
            2026,
            8,
            26,
            10,
            0,
            0,
            tzinfo=timezone(timedelta(hours=-3)),
        )
        self.record = MaterialRecord(
            material_id="MAT-001",
            description_short="  Parafuso Sextavado M8  ",
            long_description="PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
            unit="UN",
            manufacturer="ACME",
            manufacturer_part_number="ACM-825",
            material_group="FIXADORES",
            status="ACTIVE",
        )
        self.root_revision = MaterialRevision(
            revision_id="REV-001",
            record=self.record,
            revised_at=self.revised_at,
            predecessor_revision_id=None,
            source_review_id=None,
        )
        self.canonical_root_payload: dict[str, object] = {
            "schema_version": 1,
            "revision_id": "REV-001",
            "record": {
                "material_id": "MAT-001",
                "description_short": "  Parafuso Sextavado M8  ",
                "long_description": "PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
                "unit": "UN",
                "manufacturer": "ACME",
                "manufacturer_part_number": "ACM-825",
                "material_group": "FIXADORES",
                "status": "ACTIVE",
            },
            "revised_at": "2026-08-26T10:00:00-03:00",
            "predecessor_revision_id": None,
            "source_review_id": None,
        }

    def test_schema_version_constant_is_one(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)

    def test_material_revision_to_record_root_revision(self) -> None:
        payload = material_revision_to_record(self.root_revision)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["revision_id"], "REV-001")
        self.assertEqual(
            payload["revised_at"],
            "2026-08-26T10:00:00-03:00",
        )
        self.assertIsNone(payload["predecessor_revision_id"])
        self.assertIsNone(payload["source_review_id"])

        record_dict = payload["record"]
        self.assertIsInstance(record_dict, dict)
        self.assertEqual(
            record_dict,
            {
                "material_id": "MAT-001",
                "description_short": "  Parafuso Sextavado M8  ",
                "long_description": "PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
                "unit": "UN",
                "manufacturer": "ACME",
                "manufacturer_part_number": "ACM-825",
                "material_group": "FIXADORES",
                "status": "ACTIVE",
            },
        )

    def test_material_revision_from_record_root_revision(self) -> None:
        restored = material_revision_from_record(self.canonical_root_payload)

        self.assertIsInstance(restored, MaterialRevision)
        self.assertEqual(restored.revision_id, "REV-001")
        self.assertIsNone(restored.predecessor_revision_id)
        self.assertIsNone(restored.source_review_id)
        self.assertEqual(restored.material_id, "MAT-001")

        self.assertIsNotNone(restored.revised_at.tzinfo)
        self.assertIsNotNone(restored.revised_at.utcoffset())
        self.assertEqual(restored.revised_at, self.revised_at)
        self.assertEqual(
            restored.revised_at.utcoffset(),
            self.revised_at.utcoffset(),
        )

        self.assertEqual(restored.record, self.record)
        self.assertEqual(restored.record.material_id, "MAT-001")
        self.assertEqual(
            restored.record.description_short,
            "  Parafuso Sextavado M8  ",
        )
        self.assertEqual(
            restored.record.long_description,
            "PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
        )
        self.assertEqual(restored.record.unit, "UN")
        self.assertEqual(restored.record.manufacturer, "ACME")
        self.assertEqual(
            restored.record.manufacturer_part_number,
            "ACM-825",
        )
        self.assertEqual(
            restored.record.material_group,
            "FIXADORES",
        )
        self.assertEqual(restored.record.status, "ACTIVE")

    def test_round_trip_root_revision(self) -> None:
        payload = material_revision_to_record(self.root_revision)
        restored = material_revision_from_record(payload)

        self.assertEqual(restored, self.root_revision)
        self.assertEqual(restored.revision_id, self.root_revision.revision_id)
        self.assertEqual(restored.record, self.root_revision.record)
        self.assertEqual(restored.revised_at, self.root_revision.revised_at)
        self.assertEqual(
            restored.revised_at.utcoffset(),
            self.root_revision.revised_at.utcoffset(),
        )
        self.assertIsNone(restored.predecessor_revision_id)
        self.assertIsNone(restored.source_review_id)
        self.assertEqual(restored.material_id, self.root_revision.material_id)


if __name__ == "__main__":
    unittest.main()
