from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from typing import Sequence
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
    project_human_review_claim_state,
)
from agent_lab.pending_human_reviews_with_claim_state_use_case import (
    ListPendingHumanReviewsWithClaimStateUseCase,
    PendingHumanReviewWithClaimStateItem,
)
from agent_lab.workflow import GovernanceWorkflow
from agent_lab.workflow_events import (
    WorkflowLifecycleEvent,
    WorkflowOpened,
)


class FakeWorkflowLifecycleRepository:
    def __init__(self, events: Sequence[WorkflowLifecycleEvent] = ()) -> None:
        self._events = tuple(events)

    def list_all_events(self) -> tuple[WorkflowLifecycleEvent, ...]:
        return self._events


class FakeHumanReviewClaimRepository:
    def __init__(self, claims: Sequence[HumanReviewClaim] = ()) -> None:
        self._claims = tuple(claims)

    def list_all(self) -> tuple[HumanReviewClaim, ...]:
        return self._claims


class PendingHumanReviewWithClaimStateItemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Recomendação REVIEW",
            requires_human_decision=True,
        )
        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_state = project_human_review_claim_state("WF-001", ())

    def test_valid_construction_preserves_attributes(self) -> None:
        item = PendingHumanReviewWithClaimStateItem(
            workflow=self.workflow,
            claim_state=self.claim_state,
        )

        self.assertIs(item.workflow, self.workflow)
        self.assertIs(item.claim_state, self.claim_state)
        self.assertEqual(item.workflow.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.workflow_id, "WF-001")

    def test_rejects_invalid_workflow_type(self) -> None:
        invalid_workflows = [
            "not-a-workflow",
            None,
            True,
            123,
            {"workflow_id": "WF-001"},
        ]
        for invalid in invalid_workflows:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    PendingHumanReviewWithClaimStateItem(
                        workflow=invalid,  # type: ignore[arg-type]
                        claim_state=self.claim_state,
                    )

    def test_rejects_invalid_claim_state_type(self) -> None:
        invalid_claim_states = [
            "not-a-claim-state",
            None,
            True,
            123,
            (),
        ]
        for invalid in invalid_claim_states:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    PendingHumanReviewWithClaimStateItem(
                        workflow=self.workflow,
                        claim_state=invalid,  # type: ignore[arg-type]
                    )

    def test_rejects_relational_mismatch_of_workflow_id(self) -> None:
        mismatched_claim_state = project_human_review_claim_state("WF-OTHER", ())

        with self.assertRaises(ValueError) as ctx:
            PendingHumanReviewWithClaimStateItem(
                workflow=self.workflow,
                claim_state=mismatched_claim_state,
            )

        self.assertIn("WF-001", str(ctx.exception))
        self.assertIn("WF-OTHER", str(ctx.exception))

    def test_item_is_immutable(self) -> None:
        item = PendingHumanReviewWithClaimStateItem(
            workflow=self.workflow,
            claim_state=self.claim_state,
        )

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.workflow = self.workflow  # type: ignore[misc]

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.claim_state = self.claim_state  # type: ignore[misc]


class ListPendingHumanReviewsWithClaimStateUseCaseOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recommendation_1 = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Revisão necessária MAT-001",
            requires_human_decision=True,
        )
        self.recommendation_2 = DecisionRecommendation(
            material_id="MAT-002",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Revisão necessária MAT-002",
            requires_human_decision=True,
        )
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 4, 8, 0, 0, tzinfo=timezone.utc),
        )

    def test_execute_with_empty_repository_returns_empty_tuple(self) -> None:
        lifecycle_repo = FakeWorkflowLifecycleRepository(events=())
        claim_repo = FakeHumanReviewClaimRepository(claims=())
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
        )

        result = use_case.execute()

        self.assertEqual(result, ())

    def test_execute_pending_workflow_with_zero_claims_returns_no_claim_item(self) -> None:
        opened = WorkflowOpened(
            event_id="EVT-001",
            workflow_id="WF-001",
            recommendation=self.recommendation_1,
            opened_at=datetime(2026, 9, 4, 9, 0, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo = FakeWorkflowLifecycleRepository(events=(opened,))
        claim_repo = FakeHumanReviewClaimRepository(claims=())
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
        )

        result = use_case.execute()

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertIsInstance(item, PendingHumanReviewWithClaimStateItem)
        self.assertEqual(item.workflow.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.state, HumanReviewClaimFactState.NO_CLAIM)
        self.assertTrue(item.claim_state.is_unclaimed)
        self.assertFalse(item.claim_state.has_claims)
        self.assertIsNone(item.claim_state.sole_claim)

    def test_execute_pending_workflow_with_single_claim_returns_single_claim_item(self) -> None:
        opened = WorkflowOpened(
            event_id="EVT-001",
            workflow_id="WF-001",
            recommendation=self.recommendation_1,
            opened_at=datetime(2026, 9, 4, 9, 0, 0, tzinfo=timezone.utc),
        )
        claim = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 4, 9, 15, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo = FakeWorkflowLifecycleRepository(events=(opened,))
        claim_repo = FakeHumanReviewClaimRepository(claims=(claim,))
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
        )

        result = use_case.execute()

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertIsInstance(item, PendingHumanReviewWithClaimStateItem)
        self.assertEqual(item.workflow.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.state, HumanReviewClaimFactState.SINGLE_CLAIM)
        self.assertTrue(item.claim_state.has_claims)
        self.assertFalse(item.claim_state.has_multiple_claims)
        self.assertEqual(item.claim_state.sole_claim, claim)

    def test_execute_pending_workflow_with_multiple_claims_returns_multiple_claims_item(self) -> None:
        opened = WorkflowOpened(
            event_id="EVT-001",
            workflow_id="WF-001",
            recommendation=self.recommendation_1,
            opened_at=datetime(2026, 9, 4, 9, 0, 0, tzinfo=timezone.utc),
        )
        claim_1 = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 4, 9, 15, 0, tzinfo=timezone.utc),
        )
        claim_2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=datetime(2026, 9, 4, 9, 30, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo = FakeWorkflowLifecycleRepository(events=(opened,))
        claim_repo = FakeHumanReviewClaimRepository(claims=(claim_1, claim_2))
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
        )

        result = use_case.execute()

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertIsInstance(item, PendingHumanReviewWithClaimStateItem)
        self.assertEqual(item.workflow.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.workflow_id, "WF-001")
        self.assertEqual(item.claim_state.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertTrue(item.claim_state.has_multiple_claims)
        self.assertEqual(item.claim_state.claim_count, 2)
        self.assertIsNone(item.claim_state.sole_claim)

    def test_execute_multiple_workflows_preserves_canonical_queue_order(self) -> None:
        opened_later = WorkflowOpened(
            event_id="EVT-002",
            workflow_id="WF-B",
            recommendation=self.recommendation_2,
            opened_at=datetime(2026, 9, 4, 11, 0, 0, tzinfo=timezone.utc),
        )
        opened_earlier = WorkflowOpened(
            event_id="EVT-001",
            workflow_id="WF-A",
            recommendation=self.recommendation_1,
            opened_at=datetime(2026, 9, 4, 9, 0, 0, tzinfo=timezone.utc),
        )
        # Eventos fornecidos deliberadamente fora de ordem cronológica (WF-B antes de WF-A)
        lifecycle_repo = FakeWorkflowLifecycleRepository(events=(opened_later, opened_earlier))
        claim_repo = FakeHumanReviewClaimRepository(claims=())
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
        )

        result = use_case.execute()

        self.assertEqual(len(result), 2)
        # A ordem retornada deve preservar estritamente (opened_at ASC, workflow_id ASC)
        self.assertEqual(result[0].workflow.workflow_id, "WF-A")
        self.assertEqual(result[1].workflow.workflow_id, "WF-B")
