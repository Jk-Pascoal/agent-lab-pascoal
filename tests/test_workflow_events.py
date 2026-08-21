from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened


class WorkflowEventsTests(unittest.TestCase):
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
        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )
        self.review = HumanReview(
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
        )

    def build_event(self, **overrides) -> WorkflowOpened:
        values = {
            "event_id": "evt-open-001",
            "workflow_id": "wf-mat-001-01",
            "recommendation": self.recommendation,
            "opened_at": self.opened_at,
        }
        values.update(overrides)
        return WorkflowOpened(**values)

    def build_concluded_event(self, **overrides) -> WorkflowConcluded:
        values = {
            "event_id": "evt-conc-001",
            "workflow_id": "wf-mat-001-01",
            "review": self.review,
        }
        values.update(overrides)
        return WorkflowConcluded(**values)

    def test_creates_valid_workflow_opened(self) -> None:
        event = self.build_event()

        self.assertEqual(event.event_id, "evt-open-001")
        self.assertEqual(event.workflow_id, "wf-mat-001-01")
        self.assertEqual(event.recommendation, self.recommendation)
        self.assertEqual(event.opened_at, self.opened_at)

    def test_rejects_blank_event_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(event_id="")

    def test_rejects_whitespace_event_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(event_id="   ")

    def test_rejects_blank_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(workflow_id="")

    def test_rejects_whitespace_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(workflow_id="   ")

    def test_rejects_naive_opened_at(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(
                opened_at=datetime(2026, 8, 19, 8, 30, 0),
            )

    def test_rejects_invalid_recommendation_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_event(recommendation="not-a-recommendation")

    def test_is_immutable(self) -> None:
        event = self.build_event()

        with self.assertRaises(FrozenInstanceError):
            event.event_id = "evt-open-002"

    def test_creates_valid_workflow_concluded(self) -> None:
        event = self.build_concluded_event()

        self.assertEqual(event.event_id, "evt-conc-001")
        self.assertEqual(event.workflow_id, "wf-mat-001-01")
        self.assertEqual(event.review, self.review)

    def test_concluded_rejects_blank_event_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_concluded_event(event_id="")

    def test_concluded_rejects_whitespace_event_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_concluded_event(event_id="   ")

    def test_concluded_rejects_blank_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_concluded_event(workflow_id="")

    def test_concluded_rejects_whitespace_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_concluded_event(workflow_id="   ")

    def test_concluded_rejects_invalid_review_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_concluded_event(review="not-a-human-review")

    def test_concluded_is_immutable(self) -> None:
        event = self.build_concluded_event()

        with self.assertRaises(FrozenInstanceError):
            event.event_id = "evt-conc-002"


if __name__ == "__main__":
    unittest.main()
