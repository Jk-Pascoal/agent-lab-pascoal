from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision
from agent_lab.material_revision_projection import project_material_revision_lineage
from agent_lab.material_revision_repository import JsonlMaterialRevisionRepository


class MaterialRevisionLineageProjectionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "material_revisions.jsonl"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_repository_persistence_restart_and_projection(self) -> None:
        record_mat1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso Sextavado M8",
            long_description="PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
            unit="UN",
            material_group="FIXADORES",
            status="ACTIVE",
        )
        record_mat2 = MaterialRecord(
            material_id="MAT-002",
            description_short="Porca Sextavada M8",
            long_description="PORCA SEXTAVADA M8 ACO INOX",
            unit="UN",
            material_group="FIXADORES",
            status="ACTIVE",
        )

        rev_mat1_root = MaterialRevision(
            revision_id="REV-001",
            record=record_mat1,
            revised_at=datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )
        rev_mat2_root = MaterialRevision(
            revision_id="REV-002",
            record=record_mat2,
            revised_at=datetime(2026, 8, 27, 10, 15, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )
        rev_mat1_v2 = MaterialRevision(
            revision_id="REV-003",
            record=record_mat1,
            revised_at=datetime(2026, 8, 27, 10, 30, 0, tzinfo=timezone.utc),
            predecessor_revision_id="REV-001",
            source_review_id="REVW-001",
        )
        rev_mat1_v3 = MaterialRevision(
            revision_id="REV-004",
            record=record_mat1,
            revised_at=datetime(2026, 8, 27, 11, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id="REV-003",
            source_review_id="REVW-002",
        )

        # 1. Persist interspersed across materials and out-of-order physically
        repo_write = JsonlMaterialRevisionRepository(self.file_path)
        repo_write.append(rev_mat2_root)
        repo_write.append(rev_mat1_v2)
        repo_write.append(rev_mat1_root)
        repo_write.append(rev_mat1_v3)

        # 2. Simulate process restart by abandoning repo_write and opening fresh repo_read
        del repo_write
        repo_read = JsonlMaterialRevisionRepository(self.file_path)

        # 3. Read back by material
        mat1_revisions = repo_read.list_by_material("MAT-001")
        self.assertEqual(len(mat1_revisions), 3)
        # Verify physical file ordering is preserved by the repository
        self.assertEqual(
            tuple(r.revision_id for r in mat1_revisions),
            ("REV-003", "REV-001", "REV-004"),
        )

        # 4. Project lineage from rehydrated revisions
        lineage = project_material_revision_lineage(mat1_revisions)

        # 5. Verify causal topological interpretation and canonical ordering
        self.assertEqual(lineage.material_id, "MAT-001")
        self.assertEqual(
            lineage.revisions,
            (rev_mat1_root, rev_mat1_v2, rev_mat1_v3),
        )
        self.assertEqual(lineage.root_revision_ids, ("REV-001",))
        self.assertEqual(lineage.head_revision_ids, ("REV-004",))
        self.assertEqual(lineage.orphan_revision_ids, ())
        self.assertEqual(lineage.fork_predecessor_ids, ())
        self.assertEqual(lineage.cycle_revision_ids, ())

        self.assertTrue(lineage.is_linear)
        self.assertFalse(lineage.is_empty)
        self.assertFalse(lineage.has_orphans)
        self.assertFalse(lineage.has_forks)
        self.assertFalse(lineage.has_cycles)
        self.assertFalse(lineage.has_multiple_roots)
        self.assertFalse(lineage.has_ambiguities)


if __name__ == "__main__":
    unittest.main()
