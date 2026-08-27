from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_lab.domain import MaterialRecord
from agent_lab.material_revision import MaterialRevision, create_successor_revision
from agent_lab.material_revision_projection import (
    MaterialRevisionLineage,
    project_material_revision_lineage,
)


class MaterialRevisionProjectionTests(unittest.TestCase):
    def test_project_simple_linear_lineage(self) -> None:
        record1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v1",
        )
        rev1 = MaterialRevision(
            revision_id="REV-001",
            record=record1,
            revised_at=datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        record2 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v2",
        )
        rev2 = create_successor_revision(
            rev1,
            revision_id="REV-002",
            record=record2,
            revised_at=datetime(2026, 8, 27, 11, 0, 0, tzinfo=timezone.utc),
            source_review_id=None,
        )

        record3 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v3",
        )
        rev3 = create_successor_revision(
            rev2,
            revision_id="REV-003",
            record=record3,
            revised_at=datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc),
            source_review_id="REVIEW-001",
        )

        lineage = project_material_revision_lineage([rev1, rev2, rev3])

        self.assertIsInstance(lineage, MaterialRevisionLineage)
        self.assertEqual(lineage.material_id, "MAT-001")
        self.assertEqual(lineage.revisions, (rev1, rev2, rev3))
        self.assertEqual(lineage.root_revision_ids, ("REV-001",))
        self.assertEqual(lineage.head_revision_ids, ("REV-003",))
        self.assertEqual(lineage.orphan_revision_ids, ())
        self.assertEqual(lineage.fork_predecessor_ids, ())
        self.assertEqual(lineage.cycle_revision_ids, ())
        self.assertFalse(lineage.is_empty)
        self.assertTrue(lineage.is_linear)
        self.assertFalse(lineage.has_orphans)
        self.assertFalse(lineage.has_forks)
        self.assertFalse(lineage.has_multiple_roots)
        self.assertFalse(lineage.has_cycles)
        self.assertFalse(lineage.has_ambiguities)

    def test_projection_is_independent_of_input_order(self) -> None:
        record1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v1",
        )
        rev1 = MaterialRevision(
            revision_id="REV-001",
            record=record1,
            revised_at=datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        record2 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v2",
        )
        rev2 = create_successor_revision(
            rev1,
            revision_id="REV-002",
            record=record2,
            revised_at=datetime(2026, 8, 27, 11, 0, 0, tzinfo=timezone.utc),
            source_review_id=None,
        )

        record3 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v3",
        )
        rev3 = create_successor_revision(
            rev2,
            revision_id="REV-003",
            record=record3,
            revised_at=datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc),
            source_review_id="REVIEW-001",
        )

        order_a = [rev1, rev2, rev3]
        order_b = [rev3, rev1, rev2]
        order_c = [rev2, rev3, rev1]

        lineage_a = project_material_revision_lineage(order_a)
        lineage_b = project_material_revision_lineage(order_b)
        lineage_c = project_material_revision_lineage(order_c)

        self.assertEqual(lineage_a, lineage_b)
        self.assertEqual(lineage_b, lineage_c)
        self.assertEqual(lineage_a.revisions, (rev1, rev2, rev3))

    def test_detects_orphan_revision(self) -> None:
        record1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v1",
        )
        rev1 = MaterialRevision(
            revision_id="REV-001",
            record=record1,
            revised_at=datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        record2 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 com predecessor inexistente",
        )
        rev2 = MaterialRevision(
            revision_id="REV-002",
            record=record2,
            revised_at=datetime(2026, 8, 27, 11, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id="REV-999",
            source_review_id=None,
        )

        lineage = project_material_revision_lineage([rev1, rev2])

        self.assertEqual(lineage.material_id, "MAT-001")
        self.assertEqual(lineage.root_revision_ids, ("REV-001",))
        self.assertEqual(lineage.orphan_revision_ids, ("REV-002",))
        self.assertTrue(lineage.has_orphans)
        self.assertFalse(lineage.is_linear)
        self.assertTrue(lineage.has_ambiguities)
        self.assertEqual(lineage.head_revision_ids, ("REV-001", "REV-002"))

    def test_detects_forked_predecessor(self) -> None:
        record1 = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v1",
        )
        rev1 = MaterialRevision(
            revision_id="REV-001",
            record=record1,
            revised_at=datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc),
            predecessor_revision_id=None,
            source_review_id=None,
        )

        record2a = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v2 Ramo A",
        )
        rev2a = create_successor_revision(
            rev1,
            revision_id="REV-002A",
            record=record2a,
            revised_at=datetime(2026, 8, 27, 11, 0, 0, tzinfo=timezone.utc),
            source_review_id=None,
        )

        record2b = MaterialRecord(
            material_id="MAT-001",
            description_short="Parafuso M8 v2 Ramo B",
        )
        rev2b = create_successor_revision(
            rev1,
            revision_id="REV-002B",
            record=record2b,
            revised_at=datetime(2026, 8, 27, 11, 30, 0, tzinfo=timezone.utc),
            source_review_id=None,
        )

        lineage = project_material_revision_lineage([rev1, rev2a, rev2b])

        self.assertEqual(lineage.material_id, "MAT-001")
        self.assertEqual(lineage.root_revision_ids, ("REV-001",))
        self.assertEqual(
            lineage.head_revision_ids,
            ("REV-002A", "REV-002B"),
        )
        self.assertEqual(lineage.orphan_revision_ids, ())
        self.assertEqual(lineage.fork_predecessor_ids, ("REV-001",))
        self.assertTrue(lineage.has_forks)
        self.assertFalse(lineage.is_linear)
        self.assertTrue(lineage.has_ambiguities)
        self.assertFalse(lineage.has_orphans)
        self.assertFalse(lineage.has_cycles)


if __name__ == "__main__":
    unittest.main()
