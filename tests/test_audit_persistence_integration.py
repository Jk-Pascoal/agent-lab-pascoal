from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.audit import (
    AuditEventType,
    HumanReviewResult,
    record_human_review,
)
from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import HumanDecision, VerifiedSpecialistIdentity


class AuditPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "audit_history.jsonl"
        self.repository = JsonlAuditRepository(self.file_path)
        self.reviewed_at = datetime(
            2026,
            8,
            16,
            15,
            30,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            16,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-98765",
            verified_at=self.verified_at,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_end_to_end_human_review_persistence_and_recovery(self) -> None:
        result: HumanReviewResult = record_human_review(
            event_id="audit-event-001",
            review_id="review-001",
            material_id="MAT-PASCOAL-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.REJECT,
            reviewer_identity=self.reviewer_identity,
            reviewed_at=self.reviewed_at,
            justification=(
                "Classificação técnica ambígua identificada pelo especialista."
            ),
            corrections=(),
        )

        self.assertFalse(result.review.agrees_with_system)
        self.assertNotEqual(
            result.review.system_recommendation.value,
            result.review.human_decision.value,
        )

        self.repository.append(result.audit_event)

        reopened_repository = JsonlAuditRepository(self.file_path)
        retrieved_event = reopened_repository.get_by_id("audit-event-001")

        self.assertIsNotNone(retrieved_event)
        self.assertEqual(retrieved_event, result.audit_event)

        self.assertEqual(retrieved_event.event_id, "audit-event-001")
        self.assertEqual(
            retrieved_event.event_type,
            AuditEventType.HUMAN_REVIEW_RECORDED,
        )
        self.assertEqual(retrieved_event.material_id, "MAT-PASCOAL-001")
        self.assertEqual(
            retrieved_event.actor_id,
            self.reviewer_identity.specialist_id,
        )
        self.assertEqual(retrieved_event.review_id, "review-001")
        self.assertEqual(retrieved_event.occurred_at, self.reviewed_at)
        self.assertIsNotNone(retrieved_event.occurred_at.tzinfo)
        self.assertEqual(
            retrieved_event.occurred_at.tzinfo,
            timezone.utc,
        )

        self.assertEqual(
            retrieved_event.metadata["system_recommendation"],
            "APPROVE",
        )
        self.assertEqual(
            retrieved_event.metadata["human_decision"],
            "REJECT",
        )
        self.assertFalse(retrieved_event.metadata["agrees_with_system"])
        self.assertEqual(retrieved_event.metadata["correction_count"], 0)

        self.assertEqual(
            retrieved_event.metadata["identity_provider"],
            self.reviewer_identity.identity_provider,
        )
        self.assertEqual(
            retrieved_event.metadata["identity_subject"],
            self.reviewer_identity.identity_subject,
        )
        self.assertEqual(
            retrieved_event.metadata["identity_verification_id"],
            self.reviewer_identity.verification_id,
        )
        self.assertEqual(
            retrieved_event.metadata["identity_verified_at"],
            self.reviewer_identity.verified_at.isoformat(),
        )

        self.assertNotEqual(
            retrieved_event.metadata["system_recommendation"],
            retrieved_event.metadata["human_decision"],
        )


if __name__ == "__main__":
    unittest.main()
