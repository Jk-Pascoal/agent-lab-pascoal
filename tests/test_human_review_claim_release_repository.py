from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaimRelease
from agent_lab.human_review_claim_release_repository import (
    JsonlHumanReviewClaimReleaseRepository,
)


class JsonlHumanReviewClaimReleaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name) / "releases.jsonl"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_append_and_reconstitution_across_repository_instances(
        self,
    ) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        )
        release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLM-001",
            workflow_id="WF-001",
            released_by=specialist,
            released_at=datetime(2026, 9, 8, 10, 5, 0, tzinfo=timezone.utc),
        )

        repo = JsonlHumanReviewClaimReleaseRepository(self.repo_path)
        repo.append(release)

        repo2 = JsonlHumanReviewClaimReleaseRepository(self.repo_path)
        self.assertEqual(repo2.list_all(), (release,))
        self.assertEqual(repo2.get_by_id(release.release_id), release)


if __name__ == "__main__":
    unittest.main()
