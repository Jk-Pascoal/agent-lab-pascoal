from __future__ import annotations

from datetime import datetime, timezone
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.pending_human_reviews_use_case import (
    ListPendingHumanReviewsUseCase,
)
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
    WorkflowOpened,
)
from agent_lab.workflow_projection import project_pending_human_review_queue
from agent_lab.workflow_repository import WorkflowPersistenceError


class FakeWorkflowLifecycleRepository:
    def __init__(
        self,
        events: tuple[WorkflowLifecycleEvent, ...] = (),
        *,
        error: Exception | None = None,
    ) -> None:
        self.events = events
        self.error = error

    def list_all_events(self) -> tuple[WorkflowLifecycleEvent, ...]:
        if self.error is not None:
            raise self.error
        return self.events


class PendingHumanReviewsUseCaseTests(unittest.TestCase):
    def test_execute_with_empty_repository_returns_empty_tuple(self) -> None:
        repository = FakeWorkflowLifecycleRepository(events=())
        use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=repository
        )

        result = use_case.execute()

        self.assertEqual(result, ())

    def test_execute_composes_repository_events_with_canonical_projection(
        self,
    ) -> None:
        opened_at_1 = datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc)
        reviewed_at_1 = datetime(2026, 8, 30, 8, 30, 0, tzinfo=timezone.utc)
        opened_at_2 = datetime(2026, 8, 30, 9, 0, 0, tzinfo=timezone.utc)
        verified_at = datetime(2026, 8, 30, 7, 30, 0, tzinfo=timezone.utc)

        recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Recomendação REVIEW",
            requires_human_decision=True,
        )
        identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=verified_at,
        )
        review_1 = HumanReview(
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=identity,
            reviewed_at=reviewed_at_1,
            justification="Aprovado",
            corrections=(),
        )

        opened_1 = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-001",
            recommendation=recommendation,
            opened_at=opened_at_1,
        )
        concluded_1 = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id="wf-001",
            review=review_1,
        )
        opened_2 = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-002",
            recommendation=recommendation,
            opened_at=opened_at_2,
        )

        events: tuple[WorkflowLifecycleEvent, ...] = (
            opened_1,
            concluded_1,
            opened_2,
        )
        expected = project_pending_human_review_queue(events)

        repository = FakeWorkflowLifecycleRepository(events=events)
        use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=repository
        )

        actual = use_case.execute()

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0].workflow_id, "wf-002")

    def test_execute_propagates_workflow_persistence_error_from_repository(
        self,
    ) -> None:
        repository = FakeWorkflowLifecycleRepository(
            error=WorkflowPersistenceError("Simulated disk error")
        )
        use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=repository
        )

        with self.assertRaises(WorkflowPersistenceError):
            use_case.execute()

    def test_execute_propagates_projection_value_error_on_invalid_lifecycle_events(
        self,
    ) -> None:
        repository = FakeWorkflowLifecycleRepository(
            events=("not-a-lifecycle-event",)  # type: ignore[arg-type]
        )
        use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=repository
        )

        with self.assertRaises(ValueError):
            use_case.execute()


if __name__ == "__main__":
    unittest.main()
