from datetime import datetime, timedelta, timezone
import unittest

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision
from agent_lab.material_revision_serialization import (
    SCHEMA_VERSION_V1,
    material_revision_from_record,
    material_revision_to_record,
)


class MaterialRevisionSerializationTests(unittest.TestCase):
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
        self.derived_revision = MaterialRevision(
            revision_id="REV-002",
            record=self.record,
            revised_at=self.revised_at,
            predecessor_revision_id="REV-001",
            source_review_id=None,
        )
        self.canonical_derived_payload = {
            **self.canonical_root_payload,
            "revision_id": "REV-002",
            "predecessor_revision_id": "REV-001",
        }
        self.review_associated_revision = MaterialRevision(
            revision_id="REV-003",
            record=self.record,
            revised_at=self.revised_at,
            predecessor_revision_id="REV-002",
            source_review_id="REVIEW-001",
        )
        self.canonical_review_associated_payload = {
            **self.canonical_root_payload,
            "revision_id": "REV-003",
            "predecessor_revision_id": "REV-002",
            "source_review_id": "REVIEW-001",
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

    def test_material_revision_to_record_derived_revision(self) -> None:
        payload = material_revision_to_record(self.derived_revision)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["revision_id"], "REV-002")
        self.assertEqual(payload["predecessor_revision_id"], "REV-001")
        self.assertIsNone(payload["source_review_id"])
        self.assertEqual(payload["record"], self.canonical_root_payload["record"])

    def test_material_revision_from_record_derived_revision(self) -> None:
        restored = material_revision_from_record(self.canonical_derived_payload)

        self.assertEqual(restored.revision_id, "REV-002")
        self.assertEqual(restored.predecessor_revision_id, "REV-001")
        self.assertIsNone(restored.source_review_id)
        self.assertEqual(restored.record, self.record)
        self.assertEqual(restored.revised_at, self.revised_at)

    def test_round_trip_derived_revision(self) -> None:
        payload = material_revision_to_record(self.derived_revision)
        restored = material_revision_from_record(payload)

        self.assertEqual(restored, self.derived_revision)

    def test_material_revision_to_record_review_associated_revision(self) -> None:
        payload = material_revision_to_record(self.review_associated_revision)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["revision_id"], "REV-003")
        self.assertEqual(payload["predecessor_revision_id"], "REV-002")
        self.assertEqual(payload["source_review_id"], "REVIEW-001")
        self.assertEqual(payload["record"], self.canonical_root_payload["record"])

    def test_material_revision_from_record_review_associated_revision(self) -> None:
        restored = material_revision_from_record(
            self.canonical_review_associated_payload
        )

        self.assertEqual(restored.revision_id, "REV-003")
        self.assertEqual(restored.predecessor_revision_id, "REV-002")
        self.assertEqual(restored.source_review_id, "REVIEW-001")
        self.assertEqual(restored.record, self.record)
        self.assertEqual(restored.revised_at, self.revised_at)

    def test_round_trip_review_associated_revision(self) -> None:
        payload = material_revision_to_record(self.review_associated_revision)
        restored = material_revision_from_record(payload)

        self.assertEqual(restored, self.review_associated_revision)

    def test_from_record_rejects_missing_schema_version(self) -> None:
        payload = {
            k: v
            for k, v in self.canonical_root_payload.items()
            if k != "schema_version"
        }
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_unknown_schema_version(self) -> None:
        payload = {**self.canonical_root_payload, "schema_version": 2}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_string_schema_version(self) -> None:
        payload = {**self.canonical_root_payload, "schema_version": "1"}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_boolean_schema_version(self) -> None:
        payload = {**self.canonical_root_payload, "schema_version": True}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_non_mapping_envelope(self) -> None:
        with self.assertRaises(ValueError):
            material_revision_from_record([])  # type: ignore[arg-type]

    def test_from_record_rejects_non_mapping_record_field(self) -> None:
        payload = {**self.canonical_root_payload, "record": 123}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_missing_top_level_revision_id(self) -> None:
        payload = {
            k: v
            for k, v in self.canonical_root_payload.items()
            if k != "revision_id"
        }
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_non_string_material_record_fields(self) -> None:
        field_names = (
            "material_id",
            "description_short",
            "long_description",
            "unit",
            "manufacturer",
            "manufacturer_part_number",
            "material_group",
            "status",
        )
        base_record_dict = self.canonical_root_payload["record"]
        self.assertIsInstance(base_record_dict, dict)

        for field_name in field_names:
            with self.subTest(field=field_name):
                raw_record = dict(base_record_dict)
                raw_record[field_name] = 123
                payload = {
                    **self.canonical_root_payload,
                    "record": raw_record,
                }
                with self.assertRaises(ValueError):
                    material_revision_from_record(payload)

    def test_to_record_rejects_non_string_material_record_fields(self) -> None:
        field_names = (
            "material_id",
            "description_short",
            "long_description",
            "unit",
            "manufacturer",
            "manufacturer_part_number",
            "material_group",
            "status",
        )
        for field_name in field_names:
            with self.subTest(field=field_name):
                kwargs: dict[str, object] = {
                    "material_id": "MAT-001",
                    "description_short": "PARAFUSO SEXTAVADO M8",
                    "long_description": "PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
                    "unit": "UN",
                    "manufacturer": "ACME",
                    "manufacturer_part_number": "ACM-825",
                    "material_group": "FIXADORES",
                    "status": "ACTIVE",
                }
                kwargs[field_name] = 123
                if field_name == "material_id":
                    record = MaterialRecord(**kwargs)  # type: ignore[arg-type]
                    revision = object.__new__(MaterialRevision)
                    object.__setattr__(revision, "revision_id", "REV-001")
                    object.__setattr__(revision, "record", record)
                    object.__setattr__(revision, "revised_at", self.revised_at)
                    object.__setattr__(revision, "predecessor_revision_id", None)
                    object.__setattr__(revision, "source_review_id", None)
                else:
                    record = MaterialRecord(**kwargs)  # type: ignore[arg-type]
                    revision = MaterialRevision(
                        revision_id="REV-001",
                        record=record,
                        revised_at=self.revised_at,
                        predecessor_revision_id=None,
                        source_review_id=None,
                    )

                with self.assertRaises(ValueError):
                    material_revision_to_record(revision)

    def test_from_record_rejects_missing_material_record_fields(self) -> None:
        field_names = (
            "material_id",
            "description_short",
            "long_description",
            "unit",
            "manufacturer",
            "manufacturer_part_number",
            "material_group",
            "status",
        )
        base_record_dict = self.canonical_root_payload["record"]
        self.assertIsInstance(base_record_dict, dict)

        for field_name in field_names:
            with self.subTest(field=field_name):
                raw_record = {
                    k: v for k, v in base_record_dict.items() if k != field_name
                }
                payload = {
                    **self.canonical_root_payload,
                    "record": raw_record,
                }
                with self.assertRaises(ValueError):
                    material_revision_from_record(payload)

    def test_from_record_rejects_missing_top_level_envelope_fields(self) -> None:
        fields = (
            "revised_at",
            "predecessor_revision_id",
            "source_review_id",
        )
        for field_name in fields:
            with self.subTest(field=field_name):
                payload = {
                    k: v
                    for k, v in self.canonical_root_payload.items()
                    if k != field_name
                }
                with self.assertRaises(ValueError):
                    material_revision_from_record(payload)

    def test_from_record_rejects_non_string_revised_at(self) -> None:
        payload = {**self.canonical_root_payload, "revised_at": 123}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_invalid_iso_revised_at(self) -> None:
        payload = {**self.canonical_root_payload, "revised_at": "not-a-datetime"}
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_from_record_rejects_naive_revised_at(self) -> None:
        payload = {
            **self.canonical_root_payload,
            "revised_at": "2026-08-26T10:00:00",
        }
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_to_record_rejects_naive_revised_at(self) -> None:
        naive_dt = datetime(2026, 8, 26, 10, 0, 0)
        revision = object.__new__(MaterialRevision)
        object.__setattr__(revision, "revision_id", "REV-001")
        object.__setattr__(revision, "record", self.record)
        object.__setattr__(revision, "revised_at", naive_dt)
        object.__setattr__(revision, "predecessor_revision_id", None)
        object.__setattr__(revision, "source_review_id", None)

        with self.assertRaises(ValueError):
            material_revision_to_record(revision)

    def test_from_record_rejects_invalid_predecessor_revision_id_types(self) -> None:
        invalid_values = (123, True, [], {})
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                payload = {
                    **self.canonical_root_payload,
                    "predecessor_revision_id": invalid_value,
                }
                with self.assertRaises(ValueError):
                    material_revision_from_record(payload)

    def test_from_record_rejects_invalid_source_review_id_types(self) -> None:
        invalid_values = (123, True, [], {})
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                payload = {
                    **self.canonical_derived_payload,
                    "source_review_id": invalid_value,
                }
                with self.assertRaises(ValueError):
                    material_revision_from_record(payload)

    def test_from_record_rejects_source_review_id_without_predecessor(self) -> None:
        payload = {
            **self.canonical_root_payload,
            "predecessor_revision_id": None,
            "source_review_id": "REVIEW-001",
        }
        with self.assertRaises(ValueError):
            material_revision_from_record(payload)

    def test_to_record_rejects_invalid_predecessor_revision_id_types(self) -> None:
        invalid_values = (123, True, [], {})
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                revision = object.__new__(MaterialRevision)
                object.__setattr__(revision, "revision_id", "REV-002")
                object.__setattr__(revision, "record", self.record)
                object.__setattr__(revision, "revised_at", self.revised_at)
                object.__setattr__(revision, "predecessor_revision_id", invalid_value)
                object.__setattr__(revision, "source_review_id", None)

                with self.assertRaises(ValueError):
                    material_revision_to_record(revision)

    def test_to_record_rejects_invalid_source_review_id_types(self) -> None:
        invalid_values = (123, True, [], {})
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                revision = object.__new__(MaterialRevision)
                object.__setattr__(revision, "revision_id", "REV-003")
                object.__setattr__(revision, "record", self.record)
                object.__setattr__(revision, "revised_at", self.revised_at)
                object.__setattr__(revision, "predecessor_revision_id", "REV-001")
                object.__setattr__(revision, "source_review_id", invalid_value)

                with self.assertRaises(ValueError):
                    material_revision_to_record(revision)

    def test_to_record_rejects_source_review_id_without_predecessor(self) -> None:
        revision = object.__new__(MaterialRevision)
        object.__setattr__(revision, "revision_id", "REV-004")
        object.__setattr__(revision, "record", self.record)
        object.__setattr__(revision, "revised_at", self.revised_at)
        object.__setattr__(revision, "predecessor_revision_id", None)
        object.__setattr__(revision, "source_review_id", "REVIEW-001")

        with self.assertRaises(ValueError):
            material_revision_to_record(revision)


if __name__ == "__main__":
    unittest.main()
