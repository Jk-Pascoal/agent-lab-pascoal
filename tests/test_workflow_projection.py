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


if __name__ == "__main__":
    unittest.main()

