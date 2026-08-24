from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import (
    WorkflowStatus,
    conclude_governance_workflow,
    open_correction_follow_up,
)
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_projection import rehydrate_workflow
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class CorrectionFollowUpLineagePersistenceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"

        self.verified_at = datetime(
            2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc
        )
        self.wf1_opened_at = datetime(
            2026, 8, 19, 8, 30, 0, tzinfo=timezone.utc
        )
        self.wf1_reviewed_at = datetime(
            2026, 8, 19, 9, 0, 0, tzinfo=timezone.utc
        )
        self.wf2_opened_at = datetime(
            2026, 8, 19, 9, 5, 0, tzinfo=timezone.utc
        )
        self.wf2_reviewed_at = datetime(
            2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc
        )

        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@company.com",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_correction_follow_up_lineage_survives_two_restarts(self) -> None:
        material_id = "MAT-0061"

        # ────────────────────────────────────────
        # ETAPA A — WF-001 ROOT
        # ────────────────────────────────────────
        evidence_1 = (
            GovernanceEvidence(
                material_id=material_id,
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo descrição incompleto para cadastro.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation_1 = DecisionRecommendation(
            material_id=material_id,
            decision=GovernanceDecision.REVIEW,
            evidence=evidence_1,
            rationale="Recomendação REVIEW para material inicial.",
            requires_human_decision=True,
        )

        event_wf1_open = WorkflowOpened(
            event_id="evt-open-0061-001",
            workflow_id="wf-0061-001",
            recommendation=recommendation_1,
            opened_at=self.wf1_opened_at,
        )

        repository_1 = JsonlWorkflowLifecycleRepository(self.file_path)
        repository_1.append_opened(event_wf1_open)

        correction_1 = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        review_1 = HumanReview(
            review_id="rev-0061-001",
            material_id=material_id,
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.REQUEST_CORRECTION,
            reviewer_identity=self.identity,
            reviewed_at=self.wf1_reviewed_at,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction_1,),
        )

        event_wf1_conc = WorkflowConcluded(
            event_id="evt-conc-0061-001",
            workflow_id="wf-0061-001",
            review=review_1,
        )
        repository_1.append_concluded(event_wf1_conc)

        predecessor_events = repository_1.get_events_by_workflow_id(
            "wf-0061-001"
        )
        predecessor_before_follow_up = rehydrate_workflow(predecessor_events)

        self.assertEqual(
            predecessor_before_follow_up.status, WorkflowStatus.REVIEWED
        )
        self.assertEqual(predecessor_before_follow_up.review, review_1)
        self.assertIsNone(predecessor_before_follow_up.predecessor_workflow_id)
        self.assertIsNone(predecessor_before_follow_up.triggering_review_id)

        # ────────────────────────────────────────
        # ETAPA B — CRIAR WF-002 FOLLOW-UP
        # ────────────────────────────────────────
        evidence_2 = (
            GovernanceEvidence(
                material_id=material_id,
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Reavaliação pós solicitação de correção.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation_2 = DecisionRecommendation(
            material_id=material_id,
            decision=GovernanceDecision.REVIEW,
            evidence=evidence_2,
            rationale="Recomendação REVIEW para ciclo de correção.",
            requires_human_decision=True,
        )

        follow_up = open_correction_follow_up(
            predecessor_before_follow_up,
            workflow_id="wf-0061-002",
            recommendation=recommendation_2,
            opened_at=self.wf2_opened_at,
        )

        self.assertEqual(follow_up.workflow_id, "wf-0061-002")
        self.assertEqual(
            follow_up.predecessor_workflow_id, "wf-0061-001"
        )
        self.assertEqual(
            follow_up.triggering_review_id, "rev-0061-001"
        )
        self.assertEqual(
            follow_up.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        event_wf2_open = WorkflowOpened(
            event_id="evt-open-0061-002",
            workflow_id=follow_up.workflow_id,
            recommendation=follow_up.recommendation,
            opened_at=follow_up.opened_at,
            predecessor_workflow_id=follow_up.predecessor_workflow_id,
            triggering_review_id=follow_up.triggering_review_id,
        )
        repository_1.append_opened(event_wf2_open)

        # ────────────────────────────────────────
        # ETAPA C — VERIFICAR REPRESENTAÇÃO FÍSICA
        # ────────────────────────────────────────
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_lines = [line.strip() for line in f if line.strip()]

        self.assertEqual(len(raw_lines), 3)
        records = [json.loads(line) for line in raw_lines]

        record_wf2_open = records[2]
        self.assertEqual(record_wf2_open["schema_version"], 2)
        self.assertEqual(
            record_wf2_open["predecessor_workflow_id"], "wf-0061-001"
        )
        self.assertEqual(
            record_wf2_open["triggering_review_id"], "rev-0061-001"
        )
        self.assertNotIn("event_type", record_wf2_open)

        # ────────────────────────────────────────
        # ETAPA D — RESTART 1
        # ────────────────────────────────────────
        repository_2 = JsonlWorkflowLifecycleRepository(self.file_path)

        events_wf2_pending = repository_2.get_events_by_workflow_id(
            "wf-0061-002"
        )
        self.assertEqual(len(events_wf2_pending), 1)

        wf2_opened_event = events_wf2_pending[0]
        self.assertIsInstance(wf2_opened_event, WorkflowOpened)
        self.assertEqual(
            wf2_opened_event.predecessor_workflow_id, "wf-0061-001"
        )
        self.assertEqual(
            wf2_opened_event.triggering_review_id, "rev-0061-001"
        )

        pending_after_restart = rehydrate_workflow(events_wf2_pending)

        self.assertEqual(
            pending_after_restart.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(pending_after_restart.review)
        self.assertEqual(pending_after_restart.workflow_id, "wf-0061-002")
        self.assertEqual(
            pending_after_restart.predecessor_workflow_id, "wf-0061-001"
        )
        self.assertEqual(
            pending_after_restart.triggering_review_id, "rev-0061-001"
        )

        # ────────────────────────────────────────
        # ETAPA E — PREDECESSOR NÃO FOI ALTERADO
        # ────────────────────────────────────────
        events_wf1_after_restart = repository_2.get_events_by_workflow_id(
            "wf-0061-001"
        )
        predecessor_after_restart = rehydrate_workflow(
            events_wf1_after_restart
        )

        self.assertEqual(
            predecessor_after_restart, predecessor_before_follow_up
        )
        self.assertEqual(
            predecessor_after_restart.status, WorkflowStatus.REVIEWED
        )
        self.assertEqual(predecessor_after_restart.review, review_1)
        self.assertIsNone(predecessor_after_restart.predecessor_workflow_id)
        self.assertIsNone(predecessor_after_restart.triggering_review_id)

        # ────────────────────────────────────────
        # ETAPA F — CONCLUIR WF-002
        # ────────────────────────────────────────
        review_2 = HumanReview(
            review_id="rev-0061-002",
            material_id=material_id,
            system_recommendation=recommendation_2.decision,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.wf2_reviewed_at,
            justification="Correção conferida e aprovada sem ressalvas.",
            corrections=(),
        )

        reviewed_follow_up = conclude_governance_workflow(
            pending_after_restart, review_2
        )

        self.assertEqual(
            reviewed_follow_up.status, WorkflowStatus.REVIEWED
        )
        self.assertEqual(
            reviewed_follow_up.predecessor_workflow_id, "wf-0061-001"
        )
        self.assertEqual(
            reviewed_follow_up.triggering_review_id, "rev-0061-001"
        )

        event_wf2_conc = WorkflowConcluded(
            event_id="evt-conc-0061-002",
            workflow_id="wf-0061-002",
            review=review_2,
        )
        repository_2.append_concluded(event_wf2_conc)

        # ────────────────────────────────────────
        # ETAPA G — RESTART 2
        # ────────────────────────────────────────
        repository_3 = JsonlWorkflowLifecycleRepository(self.file_path)

        events_wf2_final = repository_3.get_events_by_workflow_id(
            "wf-0061-002"
        )
        self.assertEqual(len(events_wf2_final), 2)
        self.assertIsInstance(events_wf2_final[0], WorkflowOpened)
        self.assertIsInstance(events_wf2_final[1], WorkflowConcluded)

        reviewed_after_restart_2 = rehydrate_workflow(events_wf2_final)

        self.assertEqual(
            reviewed_after_restart_2.status, WorkflowStatus.REVIEWED
        )
        self.assertEqual(
            reviewed_after_restart_2.workflow_id, "wf-0061-002"
        )
        self.assertEqual(reviewed_after_restart_2.review, review_2)
        self.assertEqual(
            reviewed_after_restart_2.predecessor_workflow_id, "wf-0061-001"
        )
        self.assertEqual(
            reviewed_after_restart_2.triggering_review_id, "rev-0061-001"
        )
        self.assertEqual(
            reviewed_after_restart_2.closed_at, review_2.reviewed_at
        )
        self.assertEqual(
            reviewed_after_restart_2.review_lead_time,
            review_2.reviewed_at - follow_up.opened_at,
        )

        # ────────────────────────────────────────
        # ETAPA H — PREDECESSOR CONTINUA INTACTO
        # ────────────────────────────────────────
        events_wf1_final = repository_3.get_events_by_workflow_id(
            "wf-0061-001"
        )
        self.assertEqual(
            rehydrate_workflow(events_wf1_final),
            predecessor_before_follow_up,
        )

        all_events = repository_3.list_all_events()
        self.assertEqual(len(all_events), 4)
        self.assertEqual(all_events[0].event_id, "evt-open-0061-001")
        self.assertEqual(all_events[1].event_id, "evt-conc-0061-001")
        self.assertEqual(all_events[2].event_id, "evt-open-0061-002")
        self.assertEqual(all_events[3].event_id, "evt-conc-0061-002")


if __name__ == "__main__":
    unittest.main()
