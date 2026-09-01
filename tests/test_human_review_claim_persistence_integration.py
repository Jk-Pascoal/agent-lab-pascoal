from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

import agent_lab
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_repository import (
    DuplicateHumanReviewClaimError,
    HumanReviewClaimCorruptionError,
    HumanReviewClaimPersistenceError,
    HumanReviewClaimRepository,
    JsonlHumanReviewClaimRepository,
)
from agent_lab.human_review_claim_serialization import (
    human_review_claim_from_record,
    human_review_claim_to_record,
)


class HumanReviewClaimPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "claims_integration.jsonl"

        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-INT-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-int-123",
            verification_id="VER-INT-001",
            verified_at=datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-INT-002",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-int-456",
            verification_id="VER-INT-002",
            verified_at=datetime(2026, 8, 31, 10, 5, 0, tzinfo=timezone.utc),
        )
        self.claim_1 = HumanReviewClaim(
            claim_id="CLM-INT-001",
            workflow_id="WF-INT-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 10, 0, tzinfo=timezone.utc),
        )
        self.claim_2 = HumanReviewClaim(
            claim_id="CLM-INT-002",
            workflow_id="WF-INT-002",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 15, 0, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_round_trip_persistence_recovers_exact_claim_after_restart(self) -> None:
        # Process session 1: Write claim
        repo_session_1 = JsonlHumanReviewClaimRepository(self.storage_path)
        repo_session_1.append(self.claim_1)

        # Process session 2: New repository instance reading the same path
        repo_session_2 = JsonlHumanReviewClaimRepository(self.storage_path)
        reconstituted = repo_session_2.get_by_id("CLM-INT-001")

        self.assertIsNotNone(reconstituted)
        self.assertEqual(reconstituted, self.claim_1)
        self.assertEqual(reconstituted.claim_id, "CLM-INT-001")
        self.assertEqual(reconstituted.workflow_id, "WF-INT-001")
        self.assertEqual(reconstituted.specialist, self.specialist_1)
        self.assertEqual(reconstituted.claimed_at, self.claim_1.claimed_at)
        self.assertEqual(repo_session_2.list_all(), (self.claim_1,))

    def test_multiple_claims_with_non_utc_timezone_preserve_offsets_across_restarts(
        self,
    ) -> None:
        tz_brt = timezone(timedelta(hours=-3))
        specialist_brt = VerifiedSpecialistIdentity(
            specialist_id="SPEC-BRT",
            identity_provider="CORP-IDP-BR",
            identity_subject="user-brt-999",
            verification_id="VER-BRT-001",
            verified_at=datetime(2026, 8, 31, 7, 0, 0, tzinfo=tz_brt),
        )
        claim_brt = HumanReviewClaim(
            claim_id="CLM-BRT-001",
            workflow_id="WF-BRT-001",
            specialist=specialist_brt,
            claimed_at=datetime(2026, 8, 31, 7, 5, 0, tzinfo=tz_brt),
        )

        repo_session_1 = JsonlHumanReviewClaimRepository(self.storage_path)
        repo_session_1.append(claim_brt)

        # Restart session
        repo_session_2 = JsonlHumanReviewClaimRepository(self.storage_path)
        reconstituted = repo_session_2.get_by_id("CLM-BRT-001")

        self.assertIsNotNone(reconstituted)
        self.assertEqual(reconstituted, claim_brt)
        self.assertEqual(
            reconstituted.claimed_at.utcoffset(),
            timedelta(hours=-3),
        )
        self.assertEqual(
            reconstituted.specialist.verified_at.utcoffset(),
            timedelta(hours=-3),
        )

    def test_multiple_restarts_accumulate_claims_in_physical_order(self) -> None:
        # Restart Session 1: Append CLM-001
        repo_session_1 = JsonlHumanReviewClaimRepository(self.storage_path)
        repo_session_1.append(self.claim_1)

        # Restart Session 2: Read CLM-001 and append CLM-002
        repo_session_2 = JsonlHumanReviewClaimRepository(self.storage_path)
        self.assertEqual(repo_session_2.list_all(), (self.claim_1,))
        repo_session_2.append(self.claim_2)

        # Restart Session 3: Read both claims in strict physical append order
        repo_session_3 = JsonlHumanReviewClaimRepository(self.storage_path)
        self.assertEqual(
            repo_session_3.list_all(),
            (self.claim_1, self.claim_2),
        )

    def test_multiple_claims_for_same_workflow_retrievable_after_restart(self) -> None:
        claim_wf1_a = HumanReviewClaim(
            claim_id="CLM-INT-001",
            workflow_id="WF-INT-SHARED",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 10, 0, tzinfo=timezone.utc),
        )
        claim_wf1_b = HumanReviewClaim(
            claim_id="CLM-INT-002",
            workflow_id="WF-INT-SHARED",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 15, 0, tzinfo=timezone.utc),
        )

        repo_session_1 = JsonlHumanReviewClaimRepository(self.storage_path)
        repo_session_1.append(claim_wf1_a)
        repo_session_1.append(claim_wf1_b)

        # Restart session
        repo_session_2 = JsonlHumanReviewClaimRepository(self.storage_path)
        wf_claims = repo_session_2.list_by_workflow_id("WF-INT-SHARED")

        self.assertEqual(wf_claims, (claim_wf1_a, claim_wf1_b))
        self.assertEqual(
            repo_session_2.list_all(),
            (claim_wf1_a, claim_wf1_b),
        )

    def test_duplicate_claim_id_rejected_after_restart(self) -> None:
        repo_session_1 = JsonlHumanReviewClaimRepository(self.storage_path)
        repo_session_1.append(self.claim_1)

        # Restart session attempts to re-append same claim_id
        repo_session_2 = JsonlHumanReviewClaimRepository(self.storage_path)
        duplicate_claim = HumanReviewClaim(
            claim_id="CLM-INT-001",
            workflow_id="WF-INT-OTHER",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 20, 0, tzinfo=timezone.utc),
        )

        with self.assertRaises(DuplicateHumanReviewClaimError):
            repo_session_2.append(duplicate_claim)

        # File remains intact with exactly 1 record
        with open(self.storage_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(repo_session_2.list_all(), (self.claim_1,))

    def test_public_exports_available_from_top_level_package(self) -> None:
        # Existing exports must remain available
        self.assertTrue(hasattr(agent_lab, "HumanReviewClaim"))
        self.assertTrue(hasattr(agent_lab, "claim_pending_human_review"))
        self.assertTrue(hasattr(agent_lab, "DeterministicGovernanceValidator"))
        self.assertTrue(hasattr(agent_lab, "MaterialRecord"))

        # Serialization exports
        self.assertTrue(
            hasattr(agent_lab, "human_review_claim_to_record"),
            "human_review_claim_to_record must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.human_review_claim_to_record,
            human_review_claim_to_record,
        )
        self.assertTrue(
            hasattr(agent_lab, "human_review_claim_from_record"),
            "human_review_claim_from_record must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.human_review_claim_from_record,
            human_review_claim_from_record,
        )

        # Repository and Exception exports
        self.assertTrue(
            hasattr(agent_lab, "HumanReviewClaimPersistenceError"),
            "HumanReviewClaimPersistenceError must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.HumanReviewClaimPersistenceError,
            HumanReviewClaimPersistenceError,
        )
        self.assertTrue(
            hasattr(agent_lab, "DuplicateHumanReviewClaimError"),
            "DuplicateHumanReviewClaimError must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.DuplicateHumanReviewClaimError,
            DuplicateHumanReviewClaimError,
        )
        self.assertTrue(
            hasattr(agent_lab, "HumanReviewClaimCorruptionError"),
            "HumanReviewClaimCorruptionError must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.HumanReviewClaimCorruptionError,
            HumanReviewClaimCorruptionError,
        )
        self.assertTrue(
            hasattr(agent_lab, "HumanReviewClaimRepository"),
            "HumanReviewClaimRepository must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.HumanReviewClaimRepository,
            HumanReviewClaimRepository,
        )
        self.assertTrue(
            hasattr(agent_lab, "JsonlHumanReviewClaimRepository"),
            "JsonlHumanReviewClaimRepository must be exported by agent_lab",
        )
        self.assertIs(
            agent_lab.JsonlHumanReviewClaimRepository,
            JsonlHumanReviewClaimRepository,
        )

        # Ensure SCHEMA_VERSION_V1 is NOT exported in package root
        self.assertFalse(
            hasattr(agent_lab, "SCHEMA_VERSION_V1"),
            "SCHEMA_VERSION_V1 must NOT be exported in top-level agent_lab package",
        )
        self.assertNotIn(
            "SCHEMA_VERSION_V1",
            agent_lab.__all__,
            "SCHEMA_VERSION_V1 must NOT be included in agent_lab.__all__",
        )

        # Ensure exports in __all__
        expected_symbols = [
            "human_review_claim_to_record",
            "human_review_claim_from_record",
            "HumanReviewClaimPersistenceError",
            "DuplicateHumanReviewClaimError",
            "HumanReviewClaimCorruptionError",
            "HumanReviewClaimRepository",
            "JsonlHumanReviewClaimRepository",
        ]
        for symbol in expected_symbols:
            self.assertIn(
                symbol,
                agent_lab.__all__,
                f"{symbol} must be included in agent_lab.__all__",
            )


if __name__ == "__main__":
    unittest.main()
