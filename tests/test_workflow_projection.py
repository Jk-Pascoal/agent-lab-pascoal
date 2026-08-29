from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus
from agent_lab.workflow_events import (
    WorkflowConcluded,
    WorkflowLifecycleEvent,
    WorkflowOpened,
)
from agent_lab.workflow_projection import (
    project_pending_human_review_queue,
    rehydrate_pending_workflow,
    rehydrate_workflow,
)


class WorkflowProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            19,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            19,
            9,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence,
            rationale="Recomendação REVIEW: 1 evidência(s) requer(em) análise humana.",
            requires_human_decision=True,
        )
        self.event = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@company.com",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )
        self.review = HumanReview(
            review_id="rev-wf-mat-001-01",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification="Aprovado sem ressalvas.",
            corrections=(),
        )
        self.concluded_event = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id="wf-mat-001-01",
            review=self.review,
        )
        self.follow_up_event = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-mat-001-02",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            predecessor_workflow_id="wf-mat-001-01",
            triggering_review_id="rev-wf-mat-001-01",
        )
        self.follow_up_concluded_event = WorkflowConcluded(
            event_id="evt-conc-002",
            workflow_id="wf-mat-001-02",
            review=self.review,
        )


    def test_rehydrates_valid_workflow_opened_to_governance_workflow(self) -> None:
        workflow = rehydrate_pending_workflow(self.event)

        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, self.event.workflow_id)
        self.assertEqual(workflow.workflow_id, "wf-mat-001-01")
        self.assertIs(workflow.recommendation, self.event.recommendation)
        self.assertEqual(workflow.opened_at, self.event.opened_at)
        self.assertIsNone(workflow.review)

    def test_rehydrated_workflow_derived_properties(self) -> None:
        workflow = rehydrate_pending_workflow(self.event)

        self.assertEqual(workflow.material_id, "MAT-001")
        self.assertEqual(
            workflow.material_id,
            self.event.recommendation.material_id,
        )
        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rejects_non_workflow_opened_instance_with_type_error(self) -> None:
        with self.assertRaises(TypeError):
            rehydrate_pending_workflow("not-a-workflow-opened")  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            rehydrate_pending_workflow(None)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            rehydrate_pending_workflow(
                {
                    "event_id": "evt-001",
                    "workflow_id": "wf-001",
                    "recommendation": self.recommendation,
                    "opened_at": self.opened_at,
                }
            )  # type: ignore[arg-type]

    def test_rehydrate_workflow_from_opened_only_returns_pending(self) -> None:
        workflow = rehydrate_workflow((self.event,))

        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, self.event.workflow_id)
        self.assertEqual(workflow.workflow_id, "wf-mat-001-01")
        self.assertIs(workflow.recommendation, self.event.recommendation)
        self.assertEqual(workflow.opened_at, self.event.opened_at)
        self.assertIsNone(workflow.review)
        self.assertEqual(workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rehydrate_workflow_from_opened_and_concluded_returns_reviewed(
        self,
    ) -> None:
        workflow = rehydrate_workflow((self.event, self.concluded_event))

        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, self.event.workflow_id)
        self.assertEqual(workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(workflow.review, self.concluded_event.review)
        self.assertEqual(
            workflow.closed_at, self.concluded_event.review.reviewed_at
        )
        self.assertEqual(
            workflow.review_lead_time,
            self.concluded_event.review.reviewed_at - self.event.opened_at,
        )

    def test_rehydrate_workflow_rejects_empty_history(self) -> None:
        with self.assertRaises(ValueError):
            rehydrate_workflow(())

    def test_rehydrate_workflow_rejects_conclusion_before_opening(self) -> None:
        with self.assertRaises(ValueError):
            rehydrate_workflow((self.concluded_event, self.event))

    def test_rehydrate_workflow_rejects_multiple_openings(self) -> None:
        second_opened = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        with self.assertRaises(ValueError):
            rehydrate_workflow((self.event, second_opened))

    def test_rehydrate_workflow_rejects_multiple_conclusions(self) -> None:
        second_concluded = WorkflowConcluded(
            event_id="evt-conc-002",
            workflow_id="wf-mat-001-01",
            review=self.review,
        )
        with self.assertRaises(ValueError):
            rehydrate_workflow(
                (self.event, self.concluded_event, second_concluded)
            )

    def test_rehydrate_workflow_rejects_workflow_id_mismatch_between_events(
        self,
    ) -> None:
        mismatched_concluded = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id="wf-mat-999-99",
            review=self.review,
        )
        with self.assertRaises(ValueError):
            rehydrate_workflow((self.event, mismatched_concluded))

    def test_rehydrate_workflow_rejects_unknown_event_type(self) -> None:
        with self.assertRaises(ValueError):
            rehydrate_workflow((self.event, "not-an-event"))  # type: ignore[arg-type]

    def test_rehydrate_pending_workflow_root_has_none_lineage(self) -> None:
        workflow = rehydrate_pending_workflow(self.event)

        self.assertIsNone(workflow.predecessor_workflow_id)
        self.assertIsNone(workflow.triggering_review_id)

    def test_rehydrate_pending_workflow_preserves_follow_up_lineage(
        self,
    ) -> None:
        workflow = rehydrate_pending_workflow(self.follow_up_event)

        self.assertEqual(workflow.workflow_id, "wf-mat-001-02")
        self.assertEqual(
            workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertEqual(
            workflow.predecessor_workflow_id, "wf-mat-001-01"
        )
        self.assertEqual(
            workflow.triggering_review_id, "rev-wf-mat-001-01"
        )

    def test_rehydrate_workflow_single_event_preserves_follow_up_lineage(
        self,
    ) -> None:
        workflow = rehydrate_workflow((self.follow_up_event,))

        self.assertEqual(workflow.workflow_id, "wf-mat-001-02")
        self.assertEqual(
            workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertEqual(
            workflow.predecessor_workflow_id, "wf-mat-001-01"
        )
        self.assertEqual(
            workflow.triggering_review_id, "rev-wf-mat-001-01"
        )

    def test_rehydrate_workflow_reviewed_preserves_follow_up_lineage(
        self,
    ) -> None:
        workflow = rehydrate_workflow(
            (
                self.follow_up_event,
                self.follow_up_concluded_event,
            )
        )

        self.assertEqual(workflow.workflow_id, "wf-mat-001-02")
        self.assertEqual(workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(
            workflow.predecessor_workflow_id, "wf-mat-001-01"
        )
        self.assertEqual(
            workflow.triggering_review_id, "rev-wf-mat-001-01"
        )
        self.assertEqual(workflow.review, self.follow_up_concluded_event.review)

    def test_project_pending_queue_returns_empty_tuple_for_empty_events(
        self,
    ) -> None:
        queue = project_pending_human_review_queue(())
        self.assertEqual(queue, ())
        self.assertIsInstance(queue, tuple)

    def test_project_pending_queue_rejects_non_sequence_with_type_error(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            project_pending_human_review_queue(None)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            project_pending_human_review_queue(123)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            project_pending_human_review_queue(
                {"event": self.event}
            )  # type: ignore[arg-type]

    def test_project_pending_queue_rejects_non_lifecycle_event_with_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            project_pending_human_review_queue(
                (self.event, "not-an-event")  # type: ignore[arg-type]
            )

        with self.assertRaises(ValueError):
            project_pending_human_review_queue(
                [None]  # type: ignore[list-item]
            )

    def test_project_pending_queue_single_valid_workflow_opened(
        self,
    ) -> None:
        queue = project_pending_human_review_queue((self.event,))

        self.assertEqual(len(queue), 1)
        workflow = queue[0]
        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, self.event.workflow_id)
        self.assertIs(workflow.recommendation, self.event.recommendation)
        self.assertEqual(workflow.opened_at, self.event.opened_at)
        self.assertEqual(
            workflow.predecessor_workflow_id,
            self.event.predecessor_workflow_id,
        )
        self.assertEqual(
            workflow.triggering_review_id,
            self.event.triggering_review_id,
        )
        self.assertEqual(
            workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(workflow.review)

    def test_project_pending_queue_multiple_valid_workflows_opened(
        self,
    ) -> None:
        recommendation_2 = DecisionRecommendation(
            material_id="MAT-002",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence,
            rationale="Recomendação REVIEW MAT-002.",
            requires_human_decision=True,
        )
        event_2 = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-mat-002-01",
            recommendation=recommendation_2,
            opened_at=self.opened_at,
        )
        queue = project_pending_human_review_queue((self.event, event_2))

        self.assertEqual(len(queue), 2)
        self.assertTrue(
            all(isinstance(wf, GovernanceWorkflow) for wf in queue)
        )
        self.assertTrue(
            all(wf.status == WorkflowStatus.PENDING_HUMAN_REVIEW for wf in queue)
        )
        self.assertTrue(all(wf.review is None for wf in queue))
        workflow_ids = {wf.workflow_id for wf in queue}
        self.assertEqual(
            workflow_ids,
            {self.event.workflow_id, event_2.workflow_id},
        )

    def test_project_pending_queue_excludes_concluded_workflow(
        self,
    ) -> None:
        queue = project_pending_human_review_queue(
            (self.event, self.concluded_event)
        )
        self.assertEqual(queue, ())

    def test_project_pending_queue_retains_only_pending_when_mixed_with_concluded(
        self,
    ) -> None:
        event_pending = WorkflowOpened(
            event_id="evt-open-pending",
            workflow_id="wf-pending-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        queue = project_pending_human_review_queue(
            (self.event, self.concluded_event, event_pending)
        )
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].workflow_id, "wf-pending-01")
        self.assertEqual(
            queue[0].status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

    def test_project_pending_queue_orders_fifo_by_opened_at(
        self,
    ) -> None:
        opened_early = datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc)
        opened_late = datetime(2026, 8, 19, 9, 0, 0, tzinfo=timezone.utc)
        event_late = WorkflowOpened(
            event_id="evt-open-late",
            workflow_id="wf-late",
            recommendation=self.recommendation,
            opened_at=opened_late,
        )
        event_early = WorkflowOpened(
            event_id="evt-open-early",
            workflow_id="wf-early",
            recommendation=self.recommendation,
            opened_at=opened_early,
        )
        queue = project_pending_human_review_queue(
            (event_late, event_early)
        )
        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0].workflow_id, "wf-early")
        self.assertEqual(queue[1].workflow_id, "wf-late")

    def test_project_pending_queue_orders_lexicographically_by_workflow_id_on_same_opened_at(
        self,
    ) -> None:
        event_b = WorkflowOpened(
            event_id="evt-open-b",
            workflow_id="wf-bravo",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        event_a = WorkflowOpened(
            event_id="evt-open-a",
            workflow_id="wf-alpha",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        queue = project_pending_human_review_queue((event_b, event_a))
        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0].workflow_id, "wf-alpha")
        self.assertEqual(queue[1].workflow_id, "wf-bravo")

    def test_project_pending_queue_invariant_to_global_interleaving_preserving_internal_causality(
        self,
    ) -> None:
        opened_a = datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc)
        opened_b = datetime(2026, 8, 19, 8, 30, 0, tzinfo=timezone.utc)
        reviewed_b = datetime(2026, 8, 19, 9, 0, 0, tzinfo=timezone.utc)
        opened_c = datetime(2026, 8, 19, 9, 30, 0, tzinfo=timezone.utc)

        a_open = WorkflowOpened(
            event_id="evt-open-a",
            workflow_id="wf-a",
            recommendation=self.recommendation,
            opened_at=opened_a,
        )
        b_open = WorkflowOpened(
            event_id="evt-open-b",
            workflow_id="wf-b",
            recommendation=self.recommendation,
            opened_at=opened_b,
        )
        review_b = HumanReview(
            review_id="rev-b",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=reviewed_b,
            justification="Aprovado.",
            corrections=(),
        )
        b_concluded = WorkflowConcluded(
            event_id="evt-conc-b",
            workflow_id="wf-b",
            review=review_b,
        )
        c_open = WorkflowOpened(
            event_id="evt-open-c",
            workflow_id="wf-c",
            recommendation=self.recommendation,
            opened_at=opened_c,
        )

        sequence_1 = (a_open, b_open, b_concluded, c_open)
        sequence_2 = (b_open, a_open, c_open, b_concluded)

        queue_1 = project_pending_human_review_queue(sequence_1)
        queue_2 = project_pending_human_review_queue(sequence_2)

        self.assertEqual(queue_1, queue_2)
        self.assertEqual(len(queue_1), 2)
        self.assertEqual(queue_1[0].workflow_id, "wf-a")
        self.assertEqual(queue_1[1].workflow_id, "wf-c")
        self.assertEqual(
            {wf.workflow_id for wf in queue_1},
            {"wf-a", "wf-c"},
        )

    def test_project_pending_queue_preserves_correction_follow_up_lineage(
        self,
    ) -> None:
        queue = project_pending_human_review_queue((self.follow_up_event,))

        self.assertEqual(len(queue), 1)
        workflow = queue[0]
        self.assertIsInstance(workflow, GovernanceWorkflow)
        self.assertEqual(workflow.workflow_id, "wf-mat-001-02")
        self.assertIs(
            workflow.recommendation,
            self.follow_up_event.recommendation,
        )
        self.assertEqual(workflow.opened_at, self.follow_up_event.opened_at)
        self.assertEqual(
            workflow.predecessor_workflow_id, "wf-mat-001-01"
        )
        self.assertEqual(
            workflow.triggering_review_id, "rev-wf-mat-001-01"
        )
        self.assertEqual(
            workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(workflow.review)

    def test_project_pending_queue_rejects_conclusion_before_opening_with_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            project_pending_human_review_queue(
                (self.concluded_event, self.event)
            )

    def test_project_pending_queue_rejects_multiple_openings_with_value_error(
        self,
    ) -> None:
        second_opened = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id=self.event.workflow_id,
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        with self.assertRaises(ValueError):
            project_pending_human_review_queue(
                (self.event, second_opened)
            )

    def test_project_pending_queue_rejects_multiple_conclusions_with_value_error(
        self,
    ) -> None:
        second_concluded = WorkflowConcluded(
            event_id="evt-conc-002",
            workflow_id=self.event.workflow_id,
            review=self.review,
        )
        with self.assertRaises(ValueError):
            project_pending_human_review_queue(
                (self.event, self.concluded_event, second_concluded)
            )


if __name__ == "__main__":
    unittest.main()

