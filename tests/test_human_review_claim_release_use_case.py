from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    claim_pending_human_review,
    release_human_review_claim,
)
from agent_lab.human_review_claim_release_use_case import (
    ReleaseHumanReviewClaimUseCase,
)
from agent_lab.workflow import GovernanceWorkflow


class FakeHumanReviewClaimReleaseRepository:
    def __init__(self) -> None:
        self.appended_releases: list[HumanReviewClaimRelease] = []

    def append(self, release: HumanReviewClaimRelease) -> None:
        self.appended_releases.append(release)

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        for r in self.appended_releases:
            if r.release_id == release_id:
                return r
        return None

    def list_by_claim_id(
        self, claim_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        return tuple(
            r for r in self.appended_releases if r.claim_id == claim_id
        )

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        return tuple(
            r for r in self.appended_releases if r.workflow_id == workflow_id
        )

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        return tuple(self.appended_releases)


class ReleaseHumanReviewClaimUseCaseSlice1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeHumanReviewClaimReleaseRepository()
        self.use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=self.repository
        )

        self.verified_at = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc)
        self.claimed_at = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)
        self.released_at = datetime(2026, 9, 2, 10, 30, 0, tzinfo=timezone.utc)

        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Necessária revisão cadastral",
            requires_human_decision=True,
        )

        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            review=None,
        )

        self.claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

    def test_happy_path_coordination_creates_persists_and_returns_release(
        self,
    ) -> None:
        result = self.use_case.execute(
            self.workflow,
            self.claim,
            release_id="REL-001",
            releasing_specialist=self.specialist,
            released_at=self.released_at,
        )

        self.assertIsInstance(result, HumanReviewClaimRelease)
        self.assertEqual(result.release_id, "REL-001")
        self.assertEqual(result.claim_id, "CLM-001")
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.released_by, self.specialist)
        self.assertEqual(result.released_at, self.released_at)

        # Repositório fake recebeu exatamente um release e a mesma instância retornada
        self.assertEqual(len(self.repository.appended_releases), 1)
        self.assertIs(self.repository.appended_releases[0], result)


class ReleaseHumanReviewClaimUseCaseSlice2BoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeHumanReviewClaimReleaseRepository()
        self.use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=self.repository
        )

        self.verified_at = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc)
        self.claimed_at = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)
        self.released_at = datetime(2026, 9, 2, 10, 30, 0, tzinfo=timezone.utc)

        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Necessária revisão cadastral",
            requires_human_decision=True,
        )

        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            review=None,
        )

        self.claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

    def test_execute_rejects_non_governance_workflow_before_domain_and_io(
        self,
    ) -> None:
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(TypeError):
                self.use_case.execute(
                    object(),  # type: ignore[arg-type]
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=self.released_at,
                )

            mock_release.assert_not_called()
            self.assertEqual(len(self.repository.appended_releases), 0)

    def test_execute_rejects_non_human_review_claim_before_domain_and_io(
        self,
    ) -> None:
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(TypeError):
                self.use_case.execute(
                    self.workflow,
                    object(),  # type: ignore[arg-type]
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=self.released_at,
                )

            mock_release.assert_not_called()
            self.assertEqual(len(self.repository.appended_releases), 0)
