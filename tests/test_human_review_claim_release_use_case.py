from __future__ import annotations

from datetime import datetime, timezone
import copy
import unittest
from unittest.mock import patch

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    claim_pending_human_review,
    release_human_review_claim,
)
from agent_lab.human_review_claim_release_repository import (
    DuplicateHumanReviewClaimReleaseError,
    HumanReviewClaimReleasePersistenceError,
)
from agent_lab.human_review_claim_release_use_case import (
    ReleaseHumanReviewClaimUseCase,
)
from agent_lab.workflow import GovernanceWorkflow, conclude_governance_workflow


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


class FailingHumanReviewClaimReleaseRepository:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.append_call_count = 0
        self.last_attempted_release: HumanReviewClaimRelease | None = None

    def append(self, release: HumanReviewClaimRelease) -> None:
        self.append_call_count += 1
        self.last_attempted_release = release
        raise self.error

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        return None

    def list_by_claim_id(
        self, claim_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        return ()

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        return ()

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        return ()


class NoHistoryLookupHumanReviewClaimReleaseRepository:
    def __init__(self) -> None:
        self.appended_releases: list[HumanReviewClaimRelease] = []

    def append(self, release: HumanReviewClaimRelease) -> None:
        self.appended_releases.append(release)

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        raise AssertionError(
            "Application must not perform historical release lookup"
        )

    def list_by_claim_id(
        self, claim_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        raise AssertionError(
            "Application must not perform historical release lookup"
        )

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaimRelease, ...]:
        raise AssertionError(
            "Application must not perform historical release lookup"
        )

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        raise AssertionError(
            "Application must not perform historical release lookup"
        )


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


class ReleaseHumanReviewClaimUseCaseSlice2DomainDelegationTests(
    unittest.TestCase
):
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

    def test_execute_propagates_workflow_claim_mismatch_from_domain_with_zero_writes(
        self,
    ) -> None:
        mismatched_workflow = GovernanceWorkflow(
            workflow_id="WF-999",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            review=None,
        )
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(ValueError):
                self.use_case.execute(
                    mismatched_workflow,
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=self.released_at,
                )

            mock_release.assert_called_once()
            self.assertEqual(len(self.repository.appended_releases), 0)

    def test_execute_propagates_non_pending_workflow_rejection_from_domain_with_zero_writes(
        self,
    ) -> None:
        review = HumanReview(
            review_id="REV-001",
            material_id=self.workflow.material_id,
            system_recommendation=self.workflow.recommendation.decision,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.specialist,
            reviewed_at=datetime(2026, 9, 2, 10, 15, 0, tzinfo=timezone.utc),
        )
        concluded_workflow = conclude_governance_workflow(self.workflow, review)

        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(ValueError):
                self.use_case.execute(
                    concluded_workflow,
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=self.released_at,
                )

            mock_release.assert_called_once()
            self.assertEqual(len(self.repository.appended_releases), 0)

    def test_execute_propagates_divergent_stable_principal_from_domain_with_zero_writes(
        self,
    ) -> None:
        divergent_specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-999",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(ValueError):
                self.use_case.execute(
                    self.workflow,
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=divergent_specialist,
                    released_at=self.released_at,
                )

            mock_release.assert_called_once()
            self.assertEqual(len(self.repository.appended_releases), 0)

    def test_execute_propagates_naive_released_at_rejection_from_domain_with_zero_writes(
        self,
    ) -> None:
        naive_released_at = datetime(2026, 9, 2, 10, 30, 0)
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(ValueError):
                self.use_case.execute(
                    self.workflow,
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=naive_released_at,
                )

            mock_release.assert_called_once()
            self.assertEqual(len(self.repository.appended_releases), 0)

    def test_execute_propagates_chronology_violation_from_domain_with_zero_writes(
        self,
    ) -> None:
        earlier_released_at = datetime(2026, 9, 2, 9, 59, 0, tzinfo=timezone.utc)
        with patch(
            "agent_lab.human_review_claim_release_use_case.release_human_review_claim",
            wraps=release_human_review_claim,
        ) as mock_release:
            with self.assertRaises(ValueError):
                self.use_case.execute(
                    self.workflow,
                    self.claim,
                    release_id="REL-001",
                    releasing_specialist=self.specialist,
                    released_at=earlier_released_at,
                )

            mock_release.assert_called_once()
            self.assertEqual(len(self.repository.appended_releases), 0)


class ReleaseHumanReviewClaimUseCaseSlice3PersistenceFailureTests(
    unittest.TestCase
):
    def setUp(self) -> None:
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

    def test_execute_propagates_duplicate_release_persistence_error_without_retry_or_masking(
        self,
    ) -> None:
        expected_error = DuplicateHumanReviewClaimReleaseError(
            "duplicate release"
        )
        repository = FailingHumanReviewClaimReleaseRepository(expected_error)
        use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=repository
        )

        with self.assertRaises(DuplicateHumanReviewClaimReleaseError) as cm:
            use_case.execute(
                self.workflow,
                self.claim,
                release_id="REL-001",
                releasing_specialist=self.specialist,
                released_at=self.released_at,
            )

        self.assertIs(cm.exception, expected_error)
        self.assertEqual(repository.append_call_count, 1)
        self.assertIsInstance(
            repository.last_attempted_release, HumanReviewClaimRelease
        )
        assert repository.last_attempted_release is not None
        self.assertEqual(
            repository.last_attempted_release.release_id, "REL-001"
        )
        self.assertEqual(
            repository.last_attempted_release.claim_id, "CLM-001"
        )
        self.assertEqual(
            repository.last_attempted_release.workflow_id, "WF-001"
        )
        self.assertEqual(
            repository.last_attempted_release.released_by, self.specialist
        )
        self.assertEqual(
            repository.last_attempted_release.released_at, self.released_at
        )

    def test_execute_propagates_generic_persistence_error_without_retry_or_masking(
        self,
    ) -> None:
        expected_error = HumanReviewClaimReleasePersistenceError(
            "storage unavailable"
        )
        repository = FailingHumanReviewClaimReleaseRepository(expected_error)
        use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=repository
        )

        with self.assertRaises(HumanReviewClaimReleasePersistenceError) as cm:
            use_case.execute(
                self.workflow,
                self.claim,
                release_id="REL-001",
                releasing_specialist=self.specialist,
                released_at=self.released_at,
            )

        self.assertIs(cm.exception, expected_error)
        self.assertEqual(repository.append_call_count, 1)
        self.assertIsInstance(
            repository.last_attempted_release, HumanReviewClaimRelease
        )
        assert repository.last_attempted_release is not None
        self.assertEqual(
            repository.last_attempted_release.release_id, "REL-001"
        )
        self.assertEqual(
            repository.last_attempted_release.claim_id, "CLM-001"
        )
        self.assertEqual(
            repository.last_attempted_release.workflow_id, "WF-001"
        )
        self.assertEqual(
            repository.last_attempted_release.released_by, self.specialist
        )
        self.assertEqual(
            repository.last_attempted_release.released_at, self.released_at
        )


class ReleaseHumanReviewClaimUseCaseSlice4MultipleReleaseFactsTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.verified_at = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc)
        self.claimed_at = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)

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

    def test_execute_allows_multiple_distinct_release_facts_for_same_claim_without_history_lookup(
        self,
    ) -> None:
        repository = NoHistoryLookupHumanReviewClaimReleaseRepository()
        use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=repository
        )

        released_at_1 = datetime(2026, 9, 2, 10, 30, 0, tzinfo=timezone.utc)
        released_at_2 = datetime(2026, 9, 2, 10, 45, 0, tzinfo=timezone.utc)

        first_release = use_case.execute(
            self.workflow,
            self.claim,
            release_id="REL-001",
            releasing_specialist=self.specialist,
            released_at=released_at_1,
        )

        second_release = use_case.execute(
            self.workflow,
            self.claim,
            release_id="REL-002",
            releasing_specialist=self.specialist,
            released_at=released_at_2,
        )

        self.assertIsInstance(first_release, HumanReviewClaimRelease)
        self.assertIsInstance(second_release, HumanReviewClaimRelease)
        self.assertIsNot(first_release, second_release)

        self.assertEqual(len(repository.appended_releases), 2)
        self.assertIs(repository.appended_releases[0], first_release)
        self.assertIs(repository.appended_releases[1], second_release)

        self.assertEqual(first_release.release_id, "REL-001")
        self.assertEqual(second_release.release_id, "REL-002")

        self.assertEqual(first_release.claim_id, "CLM-001")
        self.assertEqual(second_release.claim_id, "CLM-001")
        self.assertEqual(first_release.workflow_id, "WF-001")
        self.assertEqual(second_release.workflow_id, "WF-001")

        self.assertEqual(first_release.released_by, self.specialist)
        self.assertEqual(second_release.released_by, self.specialist)

        self.assertEqual(first_release.released_at, released_at_1)
        self.assertEqual(second_release.released_at, released_at_2)


class ReleaseHumanReviewClaimUseCaseSlice5ImmutabilityTests(unittest.TestCase):
    def setUp(self) -> None:
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

    def test_execute_preserves_workflow_and_claim_without_mutation(
        self,
    ) -> None:
        repository = FakeHumanReviewClaimReleaseRepository()
        use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=repository
        )

        workflow_snapshot = copy.deepcopy(self.workflow)
        claim_snapshot = copy.deepcopy(self.claim)
        workflow_status_before = self.workflow.status
        workflow_review_before = self.workflow.review

        result = use_case.execute(
            self.workflow,
            self.claim,
            release_id="REL-001",
            releasing_specialist=self.specialist,
            released_at=self.released_at,
        )

        self.assertEqual(self.workflow, workflow_snapshot)
        self.assertEqual(self.claim, claim_snapshot)
        self.assertEqual(self.workflow.status, workflow_status_before)
        self.assertIs(self.workflow.review, workflow_review_before)
        self.assertIsNone(self.workflow.review)

        self.assertEqual(len(repository.appended_releases), 1)
        self.assertIs(repository.appended_releases[0], result)
        self.assertIsInstance(result, HumanReviewClaimRelease)

    def test_execute_preserves_workflow_and_claim_when_persistence_fails(
        self,
    ) -> None:
        expected_error = HumanReviewClaimReleasePersistenceError(
            "storage unavailable"
        )
        repository = FailingHumanReviewClaimReleaseRepository(expected_error)
        use_case = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=repository
        )

        workflow_snapshot = copy.deepcopy(self.workflow)
        claim_snapshot = copy.deepcopy(self.claim)
        workflow_status_before = self.workflow.status
        workflow_review_before = self.workflow.review

        with self.assertRaises(HumanReviewClaimReleasePersistenceError) as cm:
            use_case.execute(
                self.workflow,
                self.claim,
                release_id="REL-001",
                releasing_specialist=self.specialist,
                released_at=self.released_at,
            )

        self.assertIs(cm.exception, expected_error)
        self.assertEqual(self.workflow, workflow_snapshot)
        self.assertEqual(self.claim, claim_snapshot)
        self.assertEqual(self.workflow.status, workflow_status_before)
        self.assertIs(self.workflow.review, workflow_review_before)
        self.assertIsNone(self.workflow.review)
        self.assertEqual(repository.append_call_count, 1)
