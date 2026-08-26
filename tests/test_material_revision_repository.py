from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision
from agent_lab.material_revision_repository import (
    DuplicateMaterialRevisionError,
    JsonlMaterialRevisionRepository,
    MaterialRevisionRepository,
)
from agent_lab.material_revision_serialization import material_revision_to_record


class JsonlMaterialRevisionRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "material_revisions.jsonl"
        self.repository = JsonlMaterialRevisionRepository(self.file_path)

        self.tz = timezone(timedelta(hours=-3))

        self.record_mat1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso Sextavado M8",
            long_description="PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
            unit="UN",
            manufacturer="ACME",
            manufacturer_part_number="ACM-825",
            material_group="FIXADORES",
            status="ACTIVE",
        )
        self.record_mat2 = MaterialRecord(
            material_id="MAT-002",
            description_short="Porca Sextavada M8",
            long_description="PORCA SEXTAVADA M8 ACO INOX",
            unit="UN",
            manufacturer="ACME",
            manufacturer_part_number="ACM-800",
            material_group="FIXADORES",
            status="ACTIVE",
        )

        # Revision 1: MAT-001 (Root) at 12:00
        self.rev1 = MaterialRevision(
            revision_id="REV-001",
            record=self.record_mat1,
            revised_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=self.tz),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        # Revision 2: MAT-002 (Root) at 10:00 (earlier timestamp)
        self.rev2 = MaterialRevision(
            revision_id="REV-002",
            record=self.record_mat2,
            revised_at=datetime(2026, 8, 26, 10, 0, 0, tzinfo=self.tz),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        # Revision 3: MAT-001 (Derived from REV-001) at 11:00 (intermediate timestamp)
        self.rev3 = MaterialRevision(
            revision_id="REV-003",
            record=self.record_mat1,
            revised_at=datetime(2026, 8, 26, 11, 0, 0, tzinfo=self.tz),
            predecessor_revision_id="REV-001",
            source_review_id="REVIEW-001",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_empty_repository_returns_empty_collections_and_none_for_get_by_id(
        self,
    ) -> None:
        self.assertIsInstance(self.repository, MaterialRevisionRepository)
        self.assertIsNone(self.repository.get_by_id("UNKNOWN"))
        self.assertEqual(self.repository.list_all(), ())
        self.assertEqual(self.repository.list_by_material("UNKNOWN"), ())

    def test_append_and_get_by_id_roundtrip(self) -> None:
        self.repository.append(self.rev1)

        retrieved = self.repository.get_by_id("REV-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, self.rev1)
        self.assertIsNone(self.repository.get_by_id("REV-999"))

    def test_list_all_preserves_physical_append_order_regardless_of_revised_at(
        self,
    ) -> None:
        # Append order: rev1 (12:00), rev2 (10:00), rev3 (11:00)
        self.repository.append(self.rev1)
        self.repository.append(self.rev2)
        self.repository.append(self.rev3)

        result = self.repository.list_all()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, (self.rev1, self.rev2, self.rev3))
        self.assertEqual(
            [r.revision_id for r in result],
            ["REV-001", "REV-002", "REV-003"],
        )

    def test_list_by_material_filters_by_material_and_preserves_physical_append_order(
        self,
    ) -> None:
        # Intercalated append: MAT-001, MAT-002, MAT-001
        self.repository.append(self.rev1)
        self.repository.append(self.rev2)
        self.repository.append(self.rev3)

        mat1_revisions = self.repository.list_by_material("MAT-001")
        self.assertIsInstance(mat1_revisions, tuple)
        self.assertEqual(mat1_revisions, (self.rev1, self.rev3))

        mat2_revisions = self.repository.list_by_material("MAT-002")
        self.assertIsInstance(mat2_revisions, tuple)
        self.assertEqual(mat2_revisions, (self.rev2,))

        mat3_revisions = self.repository.list_by_material("MAT-003")
        self.assertEqual(mat3_revisions, ())

    def test_append_creates_parent_directory_and_persists_canonical_jsonl_line(
        self,
    ) -> None:
        nested_path = (
            Path(self.temp_dir.name)
            / "nested"
            / "deep"
            / "material_revisions.jsonl"
        )
        nested_repo = JsonlMaterialRevisionRepository(nested_path)

        nested_repo.append(self.rev3)

        self.assertTrue(nested_path.parent.exists())
        self.assertTrue(nested_path.exists())

        lines = nested_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)

        persisted_record = json.loads(lines[0])
        expected_record = material_revision_to_record(self.rev3)
        self.assertEqual(persisted_record, expected_record)

    def test_append_rejects_duplicate_revision_id_with_same_content(
        self,
    ) -> None:
        self.repository.append(self.rev1)

        with self.assertRaises(DuplicateMaterialRevisionError):
            self.repository.append(self.rev1)

        self.assertEqual(self.repository.list_all(), (self.rev1,))
        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)

    def test_append_rejects_duplicate_revision_id_with_different_content(
        self,
    ) -> None:
        self.repository.append(self.rev1)

        rev_diff = MaterialRevision(
            revision_id="REV-001",
            record=self.record_mat2,
            revised_at=datetime(2026, 8, 26, 14, 0, 0, tzinfo=self.tz),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        with self.assertRaises(DuplicateMaterialRevisionError):
            self.repository.append(rev_diff)

        self.assertEqual(self.repository.list_all(), (self.rev1,))
        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        persisted = json.loads(lines[0])
        self.assertEqual(persisted["record"]["material_id"], "MAT-001")

    def test_append_allows_distinct_revision_ids(self) -> None:
        self.repository.append(self.rev1)
        self.repository.append(self.rev2)

        self.assertEqual(self.repository.list_all(), (self.rev1, self.rev2))
        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
