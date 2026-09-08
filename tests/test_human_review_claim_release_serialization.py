from datetime import datetime, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaimRelease
from agent_lab.human_review_claim_release_serialization import (
    SCHEMA_VERSION_V1,
    human_review_claim_release_from_record,
    human_review_claim_release_to_record,
)


class HumanReviewClaimReleaseSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verified_at = datetime(
            2026,
            9,
            8,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.released_at = datetime(
            2026,
            9,
            8,
            10,
            5,
            0,
            tzinfo=timezone.utc,
        )
        self.released_by = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )
        self.release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLM-001",
            workflow_id="WF-001",
            released_by=self.released_by,
            released_at=self.released_at,
        )
        self.expected_canonical_record: dict[str, object] = {
            "schema_version": 1,
            "release_id": "REL-001",
            "claim_id": "CLM-001",
            "workflow_id": "WF-001",
            "released_by": {
                "specialist_id": "SPEC-001",
                "identity_provider": "CORPORATE_IDP",
                "identity_subject": "user-12345",
                "verification_id": "VER-001",
                "verified_at": "2026-09-08T10:00:00+00:00",
            },
            "released_at": "2026-09-08T10:05:00+00:00",
        }

    def test_schema_version_constant_is_one(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)
        self.assertIs(type(SCHEMA_VERSION_V1), int)

    def test_round_trip_preserves_contractual_values_and_schema_version(
        self,
    ) -> None:
        record = human_review_claim_release_to_record(self.release)

        self.assertIsInstance(record, dict)
        self.assertIs(type(record["schema_version"]), int)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["schema_version"], SCHEMA_VERSION_V1)
        self.assertEqual(record["release_id"], "REL-001")
        self.assertEqual(record["claim_id"], "CLM-001")
        self.assertEqual(record["workflow_id"], "WF-001")
        self.assertEqual(record, self.expected_canonical_record)

        reconstituted = human_review_claim_release_from_record(record)

        self.assertIsInstance(reconstituted, HumanReviewClaimRelease)
        self.assertEqual(reconstituted.release_id, self.release.release_id)
        self.assertEqual(reconstituted.claim_id, self.release.claim_id)
        self.assertEqual(reconstituted.workflow_id, self.release.workflow_id)
        self.assertEqual(reconstituted.released_by, self.release.released_by)
        self.assertEqual(reconstituted.released_at, self.release.released_at)
        self.assertEqual(reconstituted, self.release)

    def test_from_record_reads_canonical_serialized_payload(self) -> None:
        reconstituted = human_review_claim_release_from_record(
            self.expected_canonical_record
        )
        self.assertEqual(reconstituted, self.release)


if __name__ == "__main__":
    unittest.main()
