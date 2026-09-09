from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaimRelease,
    claim_pending_human_review,
)
from agent_lab.human_review_claim_release_repository import (
    JsonlHumanReviewClaimReleaseRepository,
)
from agent_lab.human_review_claim_release_use_case import (
    ReleaseHumanReviewClaimUseCase,
)
from agent_lab.workflow import GovernanceWorkflow


class ReleaseHumanReviewClaimUseCaseIntegrationTests(unittest.TestCase):
    def test_execute_persists_release_and_recovers_same_fact_after_repository_restart(
        self,
    ) -> None:
        verified_at = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        opened_at = datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc)
        claimed_at = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)
        released_at = datetime(2026, 9, 2, 10, 30, 0, tzinfo=timezone.utc)

        specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=verified_at,
        )

        recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Necessária revisão cadastral",
            requires_human_decision=True,
        )

        workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=recommendation,
            opened_at=opened_at,
            review=None,
        )

        claim = claim_pending_human_review(
            workflow,
            claim_id="CLM-001",
            specialist=specialist,
            claimed_at=claimed_at,
        )

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "human_review_claim_releases.jsonl"

            repository = JsonlHumanReviewClaimReleaseRepository(path)
            use_case = ReleaseHumanReviewClaimUseCase(
                claim_release_repository=repository
            )

            release = use_case.execute(
                workflow,
                claim,
                release_id="REL-001",
                releasing_specialist=specialist,
                released_at=released_at,
            )

            # Provas antes do restart
            self.assertIsInstance(release, HumanReviewClaimRelease)
            self.assertEqual(release.release_id, "REL-001")
            self.assertEqual(release.claim_id, "CLM-001")
            self.assertEqual(release.workflow_id, "WF-001")
            self.assertEqual(release.released_by, specialist)
            self.assertEqual(release.released_at, released_at)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

            # Restart lógico
            restarted_repository = JsonlHumanReviewClaimReleaseRepository(path)
            recovered = restarted_repository.get_by_id("REL-001")

            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered, release)
            self.assertIsNot(recovered, release)

            self.assertEqual(recovered.release_id, release.release_id)
            self.assertEqual(recovered.claim_id, release.claim_id)
            self.assertEqual(recovered.workflow_id, release.workflow_id)
            self.assertEqual(recovered.released_by, release.released_by)
            self.assertEqual(recovered.released_at, release.released_at)

            all_releases = restarted_repository.list_all()
            self.assertEqual(len(all_releases), 1)
            self.assertEqual(all_releases[0], release)
