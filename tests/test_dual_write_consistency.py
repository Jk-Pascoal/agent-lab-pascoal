from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.audit import AuditEvent, record_human_review
from agent_lab.consistency import (
    ConsistencyIssue,
    ConsistencyIssueType,
    DualWriteConsistencyReport,
    verify_dual_write_consistency,
)
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import HumanDecision, VerifiedSpecialistIdentity
from agent_lab.workflow_events import WorkflowConcluded


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


class DualWriteConsistencyFunctionTests(unittest.TestCase):
    def test_ca01_empty_collections_produce_empty_consistent_report(self) -> None:
        report = verify_dual_write_consistency([], [])

        self.assertEqual(report.total_concluded_events, 0)
        self.assertEqual(report.total_audit_review_events, 0)
        self.assertEqual(report.matched_pairs_count, 0)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.issue_count, 0)
        self.assertTrue(report.is_consistent)

    def test_ca02_single_perfect_pair_produces_consistent_report_with_matched_pair(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )

        report = verify_dual_write_consistency([concluded], [result.audit_event])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.issue_count, 0)
        self.assertTrue(report.is_consistent)

    def test_ca03_workflow_concluded_without_audit_produces_missing_audit_event(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )

        report = verify_dual_write_consistency([concluded], [])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 0)
        self.assertEqual(report.matched_pairs_count, 0)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(len(report.issues), 1)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.MISSING_AUDIT_EVENT,
        )
        self.assertEqual(issue.review_id, result.review.review_id)
        self.assertEqual(issue.workflow_id, concluded.workflow_id)
        self.assertIsNone(issue.audit_event_id)

    def test_ca04_audit_event_without_concluded_produces_missing_workflow_concluded(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )

        report = verify_dual_write_consistency([], [result.audit_event])

        self.assertEqual(report.total_concluded_events, 0)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 0)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(len(report.issues), 1)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.MISSING_WORKFLOW_CONCLUDED,
        )
        self.assertEqual(issue.review_id, result.audit_event.review_id)
        self.assertIsNone(issue.workflow_id)
        self.assertEqual(issue.audit_event_id, result.audit_event.event_id)

    def test_ca05_material_id_mismatch_produces_diagnostic_preserving_matched_pair(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )
        divergent_audit = AuditEvent(
            event_id="aud-evt-001",
            event_type=result.audit_event.event_type,
            material_id="MAT-DIFFERENT-999",
            actor_id=result.audit_event.actor_id,
            occurred_at=result.audit_event.occurred_at,
            review_id=result.audit_event.review_id,
            metadata=result.audit_event.metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(len(report.issues), 1)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.MATERIAL_ID_MISMATCH,
        )
        self.assertEqual(issue.review_id, "rev-001")
        self.assertEqual(issue.workflow_id, concluded.workflow_id)
        self.assertEqual(issue.audit_event_id, divergent_audit.event_id)

    def test_ca06_actor_id_mismatch_produces_diagnostic_preserving_matched_pair(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )
        divergent_audit = AuditEvent(
            event_id="aud-evt-001",
            event_type=result.audit_event.event_type,
            material_id=result.audit_event.material_id,
            actor_id="spec-OTHER-999",
            occurred_at=result.audit_event.occurred_at,
            review_id=result.audit_event.review_id,
            metadata=result.audit_event.metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(len(report.issues), 1)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.ACTOR_ID_MISMATCH,
        )
        self.assertEqual(issue.review_id, "rev-001")
        self.assertEqual(issue.workflow_id, concluded.workflow_id)
        self.assertEqual(issue.audit_event_id, divergent_audit.event_id)

    def test_ca07a_timestamp_mismatch_produces_diagnostic_preserving_matched_pair(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )
        different_time = datetime(2026, 8, 22, 13, 0, tzinfo=timezone.utc)
        divergent_audit = AuditEvent(
            event_id="aud-evt-001",
            event_type=result.audit_event.event_type,
            material_id=result.audit_event.material_id,
            actor_id=result.audit_event.actor_id,
            occurred_at=different_time,
            review_id=result.audit_event.review_id,
            metadata=result.audit_event.metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(len(report.issues), 1)

        issue = report.issues[0]
        self.assertEqual(
            issue.issue_type,
            ConsistencyIssueType.TIMESTAMP_MISMATCH,
        )
        self.assertEqual(issue.review_id, "rev-001")
        self.assertEqual(issue.workflow_id, concluded.workflow_id)
        self.assertEqual(issue.audit_event_id, divergent_audit.event_id)

    def test_ca07b_equivalent_timestamp_with_different_offsets_is_consistent(
        self,
    ) -> None:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )
        # 12:00 UTC == 09:00 -03:00 (mesmo instante temporal)
        tz_sp = timezone(datetime.fromisoformat("2026-08-22T00:00:00-03:00").tzinfo.utcoffset(None))  # type: ignore[union-attr]
        equivalent_time = datetime(2026, 8, 22, 9, 0, tzinfo=tz_sp)
        self.assertEqual(reviewed_at, equivalent_time)

        audit_with_offset = AuditEvent(
            event_id="aud-evt-001",
            event_type=result.audit_event.event_type,
            material_id=result.audit_event.material_id,
            actor_id=result.audit_event.actor_id,
            occurred_at=equivalent_time,
            review_id=result.audit_event.review_id,
            metadata=result.audit_event.metadata,
        )

        report = verify_dual_write_consistency([concluded], [audit_with_offset])

        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.issue_count, 0)
        self.assertTrue(report.is_consistent)

    def _create_perfect_pair(
        self,
    ) -> tuple[WorkflowConcluded, AuditEvent]:
        reviewed_at = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 22, 11, 30, tzinfo=timezone.utc)
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.com",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        result = record_human_review(
            event_id="aud-evt-001",
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at,
            justification=None,
            corrections=(),
        )
        concluded = WorkflowConcluded(
            event_id="wf-evt-001",
            workflow_id="wf-001",
            review=result.review,
        )
        return concluded, result.audit_event

    def test_ca08_test_a_perfect_metadata_is_consistent(self) -> None:
        concluded, audit = self._create_perfect_pair()
        report = verify_dual_write_consistency([concluded], [audit])

        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.issue_count, 0)
        self.assertTrue(report.is_consistent)

    def test_ca08_test_b_scalar_metadata_mismatches_produce_diagnostics(self) -> None:
        concluded, audit = self._create_perfect_pair()
        mismatch_cases = [
            ("system_recommendation", "REJECT"),
            ("human_decision", "REJECT"),
            ("agrees_with_system", False),
            ("correction_count", 3),
            ("identity_provider", "OTHER_IDP"),
            ("identity_subject", "other@corp.com"),
            ("identity_verification_id", "ver-999"),
        ]

        for field_name, divergent_value in mismatch_cases:
            with self.subTest(field=field_name):
                modified_metadata = dict(audit.metadata)
                modified_metadata[field_name] = divergent_value
                divergent_audit = AuditEvent(
                    event_id=audit.event_id,
                    event_type=audit.event_type,
                    material_id=audit.material_id,
                    actor_id=audit.actor_id,
                    occurred_at=audit.occurred_at,
                    review_id=audit.review_id,
                    metadata=modified_metadata,
                )

                report = verify_dual_write_consistency([concluded], [divergent_audit])

                self.assertEqual(report.matched_pairs_count, 1)
                self.assertEqual(report.issue_count, 1)
                self.assertFalse(report.is_consistent)
                self.assertEqual(len(report.issues), 1)

                issue = report.issues[0]
                self.assertEqual(
                    issue.issue_type,
                    ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                )
                self.assertEqual(issue.review_id, "rev-001")
                self.assertEqual(issue.workflow_id, concluded.workflow_id)
                self.assertEqual(issue.audit_event_id, audit.event_id)
                self.assertIn(field_name, issue.details)

    def test_ca08_test_c_missing_metadata_key_produces_diagnostic_without_keyerror(
        self,
    ) -> None:
        concluded, audit = self._create_perfect_pair()
        modified_metadata = dict(audit.metadata)
        del modified_metadata["system_recommendation"]

        divergent_audit = AuditEvent(
            event_id=audit.event_id,
            event_type=audit.event_type,
            material_id=audit.material_id,
            actor_id=audit.actor_id,
            occurred_at=audit.occurred_at,
            review_id=audit.review_id,
            metadata=modified_metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(
            report.issues[0].issue_type,
            ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
        )
        self.assertIn("system_recommendation", report.issues[0].details)

    def test_ca08_test_d_incompatible_metadata_type_produces_diagnostic(self) -> None:
        concluded, audit = self._create_perfect_pair()
        modified_metadata = dict(audit.metadata)
        modified_metadata["correction_count"] = "not-an-integer"

        divergent_audit = AuditEvent(
            event_id=audit.event_id,
            event_type=audit.event_type,
            material_id=audit.material_id,
            actor_id=audit.actor_id,
            occurred_at=audit.occurred_at,
            review_id=audit.review_id,
            metadata=modified_metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(
            report.issues[0].issue_type,
            ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
        )
        self.assertIn("correction_count", report.issues[0].details)

    def test_ca08_test_e_divergent_identity_verified_at_produces_diagnostic(
        self,
    ) -> None:
        concluded, audit = self._create_perfect_pair()
        modified_metadata = dict(audit.metadata)
        modified_metadata["identity_verified_at"] = (
            "2026-08-22T15:00:00+00:00"  # diferente de 11:30
        )

        divergent_audit = AuditEvent(
            event_id=audit.event_id,
            event_type=audit.event_type,
            material_id=audit.material_id,
            actor_id=audit.actor_id,
            occurred_at=audit.occurred_at,
            review_id=audit.review_id,
            metadata=modified_metadata,
        )

        report = verify_dual_write_consistency([concluded], [divergent_audit])

        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issue_count, 1)
        self.assertFalse(report.is_consistent)
        self.assertEqual(
            report.issues[0].issue_type,
            ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
        )
        self.assertIn("identity_verified_at", report.issues[0].details)

    def test_ca08_test_f_equivalent_identity_verified_at_different_offset_is_consistent(
        self,
    ) -> None:
        concluded, audit = self._create_perfect_pair()
        # 11:30 UTC == 08:30 -03:00
        modified_metadata = dict(audit.metadata)
        modified_metadata["identity_verified_at"] = "2026-08-22T08:30:00-03:00"

        audit_with_offset = AuditEvent(
            event_id=audit.event_id,
            event_type=audit.event_type,
            material_id=audit.material_id,
            actor_id=audit.actor_id,
            occurred_at=audit.occurred_at,
            review_id=audit.review_id,
            metadata=modified_metadata,
        )

        report = verify_dual_write_consistency([concluded], [audit_with_offset])

        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())
        self.assertEqual(report.issue_count, 0)
        self.assertTrue(report.is_consistent)

    def test_ca08_test_g_invalid_or_naive_identity_verified_at_produces_diagnostic(
        self,
    ) -> None:
        concluded, audit = self._create_perfect_pair()
        invalid_values = [
            "invalid-isoformat-string",
            "2026-08-22T11:30:00",  # naive, sem fuso/offset
            123456789,  # não é string
        ]

        for invalid_val in invalid_values:
            with self.subTest(invalid_value=invalid_val):
                modified_metadata = dict(audit.metadata)
                modified_metadata["identity_verified_at"] = invalid_val

                divergent_audit = AuditEvent(
                    event_id=audit.event_id,
                    event_type=audit.event_type,
                    material_id=audit.material_id,
                    actor_id=audit.actor_id,
                    occurred_at=audit.occurred_at,
                    review_id=audit.review_id,
                    metadata=modified_metadata,
                )

                report = verify_dual_write_consistency([concluded], [divergent_audit])

                self.assertEqual(report.matched_pairs_count, 1)
                self.assertEqual(report.issue_count, 1)
                self.assertFalse(report.is_consistent)
                self.assertEqual(
                    report.issues[0].issue_type,
                    ConsistencyIssueType.AUDIT_METADATA_MISMATCH,
                )
                self.assertIn("identity_verified_at", report.issues[0].details)


if __name__ == "__main__":
    unittest.main()

