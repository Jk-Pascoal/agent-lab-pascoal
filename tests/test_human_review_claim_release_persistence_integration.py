from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import agent_lab
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    claim_pending_human_review,
    release_human_review_claim,
)
from agent_lab.human_review_claim_release_repository import (
    DuplicateHumanReviewClaimReleaseError,
    HumanReviewClaimReleaseCorruptionError,
    HumanReviewClaimReleasePersistenceError,
    HumanReviewClaimReleaseRepository,
    JsonlHumanReviewClaimReleaseRepository,
)
from agent_lab.human_review_claim_release_serialization import (
    human_review_claim_release_from_record,
    human_review_claim_release_to_record,
)
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class HumanReviewClaimReleasePublicApiTests(unittest.TestCase):
    def test_public_api_exports_and_all_membership(self) -> None:
        # Verify package root attributes and instances
        self.assertIs(
            agent_lab.human_review_claim_release_to_record,
            human_review_claim_release_to_record,
        )
        self.assertIs(
            agent_lab.human_review_claim_release_from_record,
            human_review_claim_release_from_record,
        )
        self.assertIs(
            agent_lab.HumanReviewClaimReleasePersistenceError,
            HumanReviewClaimReleasePersistenceError,
        )
        self.assertIs(
            agent_lab.DuplicateHumanReviewClaimReleaseError,
            DuplicateHumanReviewClaimReleaseError,
        )
        self.assertIs(
            agent_lab.HumanReviewClaimReleaseCorruptionError,
            HumanReviewClaimReleaseCorruptionError,
        )
        self.assertIs(
            agent_lab.HumanReviewClaimReleaseRepository,
            HumanReviewClaimReleaseRepository,
        )
        self.assertIs(
            agent_lab.JsonlHumanReviewClaimReleaseRepository,
            JsonlHumanReviewClaimReleaseRepository,
        )

        # Ensure SCHEMA_VERSION_V1 is NOT exported in top-level package root
        self.assertNotIn(
            "SCHEMA_VERSION_V1",
            agent_lab.__all__,
            "SCHEMA_VERSION_V1 must NOT be included in agent_lab.__all__",
        )

        # Ensure all 7 symbols are in agent_lab.__all__
        expected_symbols = [
            "human_review_claim_release_to_record",
            "human_review_claim_release_from_record",
            "HumanReviewClaimReleasePersistenceError",
            "DuplicateHumanReviewClaimReleaseError",
            "HumanReviewClaimReleaseCorruptionError",
            "HumanReviewClaimReleaseRepository",
            "JsonlHumanReviewClaimReleaseRepository",
        ]
        for symbol in expected_symbols:
            self.assertIn(
                symbol,
                agent_lab.__all__,
                f"{symbol} must be included in agent_lab.__all__",
            )


class HumanReviewClaimReleasePersistenceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = (
            Path(self.temp_dir.name) / "releases_integration.jsonl"
        )

        self.verified_at = datetime(
            2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc
        )
        self.opened_at = datetime(
            2026, 9, 8, 10, 2, 0, tzinfo=timezone.utc
        )
        self.claimed_at = datetime(
            2026, 9, 8, 10, 5, 0, tzinfo=timezone.utc
        )
        self.released_at_1 = datetime(
            2026, 9, 8, 10, 10, 0, tzinfo=timezone.utc
        )
        self.released_at_2 = datetime(
            2026, 9, 8, 10, 15, 0, tzinfo=timezone.utc
        )

        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="corp-idp",
            identity_subject="specialist@corp.local",
            verification_id="ver-12345",
            verified_at=self.verified_at,
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0001",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação de teste",
            requires_human_decision=True,
        )
        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        self.claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLAIM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_round_trip_release_persistence_recovers_canonical_release_across_repository_instances(
        self,
    ) -> None:
        self.assertEqual(
            self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(self.workflow.review)
        self.assertIsInstance(self.claim, HumanReviewClaim)
        self.assertEqual(self.claim.claim_id, "CLAIM-001")

        release = release_human_review_claim(
            self.workflow,
            self.claim,
            release_id="REL-INT-001",
            releasing_specialist=self.specialist,
            released_at=self.released_at_1,
        )
        self.assertIsInstance(release, HumanReviewClaimRelease)

        repo_session_1 = JsonlHumanReviewClaimReleaseRepository(
            self.storage_path
        )
        repo_session_1.append(release)

        repo_session_2 = JsonlHumanReviewClaimReleaseRepository(
            self.storage_path
        )
        reconstituted = repo_session_2.get_by_id("REL-INT-001")

        self.assertIsNotNone(reconstituted)
        self.assertEqual(reconstituted, release)
        self.assertEqual(reconstituted.release_id, "REL-INT-001")
        self.assertEqual(reconstituted.claim_id, "CLAIM-001")
        self.assertEqual(reconstituted.workflow_id, "WF-001")
        self.assertEqual(reconstituted.released_by, self.specialist)
        self.assertEqual(reconstituted.released_at, self.released_at_1)

        self.assertEqual(repo_session_2.list_all(), (release,))
        self.assertEqual(
            repo_session_2.list_by_claim_id("CLAIM-001"), (release,)
        )
        self.assertEqual(
            repo_session_2.list_by_workflow_id("WF-001"), (release,)
        )

        # Confirm original workflow and claim remain intact
        self.assertEqual(self.workflow.workflow_id, "WF-001")
        self.assertEqual(
            self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(self.workflow.review)
        self.assertEqual(self.claim.claim_id, "CLAIM-001")
        self.assertEqual(self.claim.workflow_id, "WF-001")
        self.assertEqual(self.claim.specialist, self.specialist)
        self.assertEqual(self.claim.claimed_at, self.claimed_at)

    def test_two_distinct_releases_for_same_claim_are_persisted_and_recovered(
        self,
    ) -> None:
        release_1 = release_human_review_claim(
            self.workflow,
            self.claim,
            release_id="REL-INT-001",
            releasing_specialist=self.specialist,
            released_at=self.released_at_1,
        )
        release_2 = release_human_review_claim(
            self.workflow,
            self.claim,
            release_id="REL-INT-002",
            releasing_specialist=self.specialist,
            released_at=self.released_at_2,
        )

        repo_session_1 = JsonlHumanReviewClaimReleaseRepository(
            self.storage_path
        )
        repo_session_1.append(release_1)
        repo_session_1.append(release_2)

        repo_session_2 = JsonlHumanReviewClaimReleaseRepository(
            self.storage_path
        )
        self.assertEqual(repo_session_2.list_all(), (release_1, release_2))
        self.assertEqual(
            repo_session_2.list_by_claim_id("CLAIM-001"),
            (release_1, release_2),
        )
        self.assertEqual(
            repo_session_2.list_by_workflow_id("WF-001"),
            (release_1, release_2),
        )
        self.assertEqual(
            repo_session_2.get_by_id("REL-INT-001"), release_1
        )
        self.assertEqual(
            repo_session_2.get_by_id("REL-INT-002"), release_2
        )


if __name__ == "__main__":
    unittest.main()
