from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from agent_lab.consistency import (
    ConsistencyIssue,
    ConsistencyIssueType,
    DualWriteConsistencyReport,
)


class ConsistencyContractsTests(unittest.TestCase):
    def test_consistency_issue_type_defines_all_eight_canonical_members(self) -> None:
        expected_members = {
            "MISSING_AUDIT_EVENT": "MISSING_AUDIT_EVENT",
            "MISSING_WORKFLOW_CONCLUDED": "MISSING_WORKFLOW_CONCLUDED",
            "MATERIAL_ID_MISMATCH": "MATERIAL_ID_MISMATCH",
            "ACTOR_ID_MISMATCH": "ACTOR_ID_MISMATCH",
            "TIMESTAMP_MISMATCH": "TIMESTAMP_MISMATCH",
            "AUDIT_METADATA_MISMATCH": "AUDIT_METADATA_MISMATCH",
            "DUPLICATE_REVIEW_ID_IN_LIFECYCLE": "DUPLICATE_REVIEW_ID_IN_LIFECYCLE",
            "DUPLICATE_REVIEW_ID_IN_AUDIT": "DUPLICATE_REVIEW_ID_IN_AUDIT",
        }

        self.assertEqual(len(ConsistencyIssueType), 8)
        for name, value in expected_members.items():
            member = getattr(ConsistencyIssueType, name, None)
            self.assertIsNotNone(member)
            self.assertEqual(member.value, value)

    def test_consistency_issue_instantiation_fields_and_immutability(self) -> None:
        issue = ConsistencyIssue(
            issue_type=ConsistencyIssueType.MATERIAL_ID_MISMATCH,
            review_id="rev-001",
            workflow_id="wf-001",
            audit_event_id="aud-001",
            details="Material ID mismatch: MAT-1 != MAT-2",
        )

        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.MATERIAL_ID_MISMATCH,
        )
        self.assertEqual(issue.review_id, "rev-001")
        self.assertEqual(issue.workflow_id, "wf-001")
        self.assertEqual(issue.audit_event_id, "aud-001")
        self.assertEqual(
            issue.details,
            "Material ID mismatch: MAT-1 != MAT-2",
        )

        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            issue.review_id = "rev-002"  # type: ignore[misc]

    def test_dual_write_consistency_report_instantiation_properties_and_immutability(
        self,
    ) -> None:
        issue = ConsistencyIssue(
            issue_type=ConsistencyIssueType.MISSING_AUDIT_EVENT,
            review_id="rev-001",
            workflow_id="wf-001",
            audit_event_id=None,
            details="AuditEvent missing for review_id rev-001",
        )

        inconsistent_report = DualWriteConsistencyReport(
            total_concluded_events=1,
            total_audit_review_events=0,
            matched_pairs_count=0,
            issues=(issue,),
        )

        self.assertEqual(inconsistent_report.total_concluded_events, 1)
        self.assertEqual(inconsistent_report.total_audit_review_events, 0)
        self.assertEqual(inconsistent_report.matched_pairs_count, 0)
        self.assertEqual(inconsistent_report.issues, (issue,))
        self.assertEqual(inconsistent_report.issue_count, 1)
        self.assertFalse(inconsistent_report.is_consistent)

        consistent_report = DualWriteConsistencyReport(
            total_concluded_events=2,
            total_audit_review_events=2,
            matched_pairs_count=2,
            issues=(),
        )

        self.assertEqual(consistent_report.total_concluded_events, 2)
        self.assertEqual(consistent_report.total_audit_review_events, 2)
        self.assertEqual(consistent_report.matched_pairs_count, 2)
        self.assertEqual(consistent_report.issues, ())
        self.assertEqual(consistent_report.issue_count, 0)
        self.assertTrue(consistent_report.is_consistent)

        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            consistent_report.matched_pairs_count = 3  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
