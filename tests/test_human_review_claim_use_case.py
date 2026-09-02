from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_repository import (
    HumanReviewClaimPersistenceError,
)
from agent_lab.human_review_claim_use_case import RecordHumanReviewClaimUseCase
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class FakeHumanReviewClaimRepository:
    def __init__(self) -> None:
        self.appended_claims: list[HumanReviewClaim] = []

    def append(self, claim: HumanReviewClaim) -> None:
        self.appended_claims.append(claim)

    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None:
        for c in self.appended_claims:
            if c.claim_id == claim_id:
                return c
        return None

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaim, ...]:
        return tuple(
            c for c in self.appended_claims if c.workflow_id == workflow_id
        )

    def list_all(self) -> tuple[HumanReviewClaim, ...]:
        return tuple(self.appended_claims)


class RecordHumanReviewClaimUseCaseSlice1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeHumanReviewClaimRepository()
        self.use_case = RecordHumanReviewClaimUseCase(
            claim_repository=self.repository
        )

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

    def test_happy_path_coordination_creates_and_persists_claim(self) -> None:
        result = self.use_case.execute(
            self.workflow,
            claim_id="CLM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

        self.assertIsInstance(result, HumanReviewClaim)
        self.assertEqual(result.claim_id, "CLM-001")
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.specialist, self.specialist)
        self.assertEqual(result.claimed_at, self.claimed_at)

        # Repositório recebeu exatamente o claim retornado
        self.assertEqual(len(self.repository.appended_claims), 1)
        self.assertIs(self.repository.appended_claims[0], result)

        # Workflow permanece estritamente inalterado e em PENDING_HUMAN_REVIEW
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(self.workflow.review)
        self.assertEqual(self.workflow.workflow_id, "WF-001")
        self.assertEqual(self.workflow.opened_at, self.opened_at)


class RecordHumanReviewClaimUseCaseSlice2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeHumanReviewClaimRepository()
        self.use_case = RecordHumanReviewClaimUseCase(
            claim_repository=self.repository
        )

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

    def test_execute_rejects_non_governance_workflow_before_domain_and_io(self) -> None:
        with patch(
            "agent_lab.human_review_claim_use_case.claim_pending_human_review"
        ) as mock_claim:
            with self.assertRaises(TypeError) as ctx:
                self.use_case.execute(
                    object(),  # type: ignore[arg-type]
                    claim_id="CLM-001",
                    specialist=self.specialist,
                    claimed_at=self.claimed_at,
                )

            self.assertEqual(str(ctx.exception), "workflow must be a GovernanceWorkflow")
            mock_claim.assert_not_called()
            self.assertEqual(len(self.repository.appended_claims), 0)

    def test_execute_propagates_domain_chronology_error_without_io(self) -> None:
        invalid_claimed_at = self.opened_at.replace(minute=29)

        with self.assertRaises(ValueError) as ctx:
            self.use_case.execute(
                self.workflow,
                claim_id="CLM-001",
                specialist=self.specialist,
                claimed_at=invalid_claimed_at,
            )

        self.assertIn("claimed_at must not be before workflow opened_at", str(ctx.exception))
        self.assertEqual(len(self.repository.appended_claims), 0)
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(self.workflow.review)


class FailingHumanReviewClaimRepository:
    def __init__(self, error_to_raise: Exception) -> None:
        self.error_to_raise = error_to_raise
        self.append_calls: list[HumanReviewClaim] = []

    def append(self, claim: HumanReviewClaim) -> None:
        self.append_calls.append(claim)
        raise self.error_to_raise

    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None:
        return None

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaim, ...]:
        return ()

    def list_all(self) -> tuple[HumanReviewClaim, ...]:
        return ()


class RecordHumanReviewClaimUseCaseSlice3Tests(unittest.TestCase):
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

    def test_execute_propagates_repository_persistence_error_fail_closed(self) -> None:
        expected_error = HumanReviewClaimPersistenceError("simulated persistence failure")
        failing_repo = FailingHumanReviewClaimRepository(error_to_raise=expected_error)
        use_case = RecordHumanReviewClaimUseCase(claim_repository=failing_repo)

        with self.assertRaises(HumanReviewClaimPersistenceError) as ctx:
            use_case.execute(
                self.workflow,
                claim_id="CLM-001",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

        self.assertIs(ctx.exception, expected_error)
        self.assertEqual(str(ctx.exception), "simulated persistence failure")

        # append chamado exatamente uma vez (sem retries)
        self.assertEqual(len(failing_repo.append_calls), 1)
        received_claim = failing_repo.append_calls[0]
        self.assertIsInstance(received_claim, HumanReviewClaim)
        self.assertEqual(received_claim.claim_id, "CLM-001")
        self.assertEqual(received_claim.workflow_id, "WF-001")
        self.assertEqual(received_claim.specialist, self.specialist)
        self.assertEqual(received_claim.claimed_at, self.claimed_at)

        # workflow permanece estritamente inalterado
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(self.workflow.review)
        self.assertEqual(self.workflow.workflow_id, "WF-001")
        self.assertEqual(self.workflow.opened_at, self.opened_at)
