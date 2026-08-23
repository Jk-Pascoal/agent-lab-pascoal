from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from agent_lab import workflow as workflow_module
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class GovernanceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            18,
            9,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            45,
            0,
            tzinfo=timezone.utc,
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação APPROVE para teste.",
            requires_human_decision=True,
        )
        self.reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-12345",
            verified_at=self.verified_at,
        )

    def build_workflow(self, **overrides) -> GovernanceWorkflow:
        values = {
            "workflow_id": "wf-001",
            "recommendation": self.recommendation,
            "opened_at": self.opened_at,
            "review": None,
        }
        values.update(overrides)
        return GovernanceWorkflow(**values)

    def build_review(self, **overrides) -> HumanReview:
        values = {
            "review_id": "rev-001",
            "material_id": "MAT-0044",
            "system_recommendation": GovernanceDecision.APPROVE,
            "human_decision": HumanDecision.APPROVE,
            "reviewer_identity": self.reviewer_identity,
            "reviewed_at": self.reviewed_at,
            "justification": None,
            "corrections": (),
        }
        values.update(overrides)
        return HumanReview(**values)

    def test_creates_valid_pending_workflow(self) -> None:
        workflow = self.build_workflow()

        self.assertEqual(workflow.workflow_id, "wf-001")
        self.assertEqual(workflow.recommendation, self.recommendation)
        self.assertEqual(workflow.opened_at, self.opened_at)
        self.assertIsNone(workflow.review)

    def test_new_workflow_derived_properties(self) -> None:
        workflow = self.build_workflow()

        self.assertEqual(workflow.material_id, "MAT-0044")
        self.assertEqual(
            workflow.material_id,
            self.recommendation.material_id,
        )
        self.assertEqual(
            workflow.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow.closed_at)
        self.assertIsNone(workflow.review_lead_time)

    def test_rejects_blank_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(workflow_id="")

    def test_rejects_whitespace_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(workflow_id="   ")

    def test_rejects_naive_opened_at(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(
                opened_at=datetime(2026, 8, 18, 10, 0, 0),
            )

    def test_rejects_invalid_recommendation_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(recommendation="not-a-recommendation")

    def test_is_immutable(self) -> None:
        workflow = self.build_workflow()

        with self.assertRaises(FrozenInstanceError):
            workflow.workflow_id = "wf-002"

    def test_rejects_invalid_review_type(self) -> None:
        with self.assertRaises(ValueError):
            self.build_workflow(review="not-a-human-review")

    def test_rejects_review_with_different_material_id(self) -> None:
        review = self.build_review(material_id="MAT-OTHER")
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_rejects_review_with_different_system_recommendation(self) -> None:
        review = self.build_review(
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
        )
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_rejects_review_before_opened_at(self) -> None:
        earlier_reviewed_at = datetime(
            2026,
            8,
            18,
            9,
            45,
            0,
            tzinfo=timezone.utc,
        )
        earlier_identity = VerifiedSpecialistIdentity(
            specialist_id="specialist-001",
            identity_provider="corporate-idp",
            identity_subject="user@corp.local",
            verification_id="assert-12345",
            verified_at=datetime(2026, 8, 18, 9, 30, 0, tzinfo=timezone.utc),
        )
        review = self.build_review(
            reviewed_at=earlier_reviewed_at,
            reviewer_identity=earlier_identity,
        )
        with self.assertRaises(ValueError):
            self.build_workflow(review=review)

    def test_conclude_returns_new_workflow_and_leaves_original_unmodified(
        self,
    ) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertIsNot(concluded, original)
        self.assertIsNone(original.review)
        self.assertEqual(original.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(original.closed_at)
        self.assertIsNone(original.review_lead_time)

    def test_concluded_workflow_preserves_identifiers_and_sets_review_and_status(
        self,
    ) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertEqual(concluded.workflow_id, original.workflow_id)
        self.assertEqual(concluded.recommendation, original.recommendation)
        self.assertEqual(concluded.material_id, original.material_id)
        self.assertEqual(concluded.opened_at, original.opened_at)
        self.assertEqual(concluded.review, review)
        self.assertEqual(concluded.status, WorkflowStatus.REVIEWED)

    def test_concluded_workflow_derived_temporal_properties(self) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        self.assertEqual(concluded.closed_at, self.reviewed_at)
        expected_lead_time = self.reviewed_at - self.opened_at
        self.assertEqual(concluded.review_lead_time, expected_lead_time)
        self.assertEqual(concluded.review_lead_time, timedelta(minutes=45))

    def test_conclude_rejects_already_reviewed_workflow(self) -> None:
        original = self.build_workflow()
        review = self.build_review()

        concluded = workflow_module.conclude_governance_workflow(
            original, review
        )

        second_review = self.build_review(review_id="rev-002")
        with self.assertRaises(ValueError):
            workflow_module.conclude_governance_workflow(
                concluded, second_review
            )

    def test_open_correction_follow_up_creates_pending_successor_linked_to_predecessor(
        self,
    ) -> None:
        predecessor_opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=predecessor_opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        predecessor_reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            30,
            0,
            tzinfo=timezone.utc,
        )
        review = self.build_review(
            review_id="rev-001",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=predecessor_reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )

        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )
        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação após submissão de correções.",
            requires_human_decision=True,
        )

        successor = workflow_module.open_correction_follow_up(
            concluded_predecessor,
            workflow_id="wf-002",
            recommendation=follow_up_recommendation,
            opened_at=follow_up_opened_at,
        )

        self.assertEqual(successor.workflow_id, "wf-002")
        self.assertNotEqual(
            successor.workflow_id, concluded_predecessor.workflow_id
        )
        self.assertEqual(
            successor.material_id, concluded_predecessor.material_id
        )
        self.assertEqual(
            successor.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(successor.review)
        self.assertEqual(
            successor.predecessor_workflow_id,
            concluded_predecessor.workflow_id,
        )
        self.assertEqual(
            successor.triggering_review_id, review.review_id
        )

        # Predecessor permanece inalterado
        self.assertEqual(concluded_predecessor.workflow_id, "wf-001")
        self.assertEqual(
            concluded_predecessor.status, WorkflowStatus.REVIEWED
        )
        self.assertEqual(concluded_predecessor.review, review)

    def test_open_correction_follow_up_rejects_pending_predecessor(
        self,
    ) -> None:
        pending_predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=self.opened_at,
        )
        self.assertEqual(
            pending_predecessor.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )

        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação para follow-up.",
            requires_human_decision=True,
        )
        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            workflow_module.open_correction_follow_up(
                pending_predecessor,
                workflow_id="wf-002",
                recommendation=follow_up_recommendation,
                opened_at=follow_up_opened_at,
            )

    def test_open_correction_follow_up_rejects_non_correction_decisions(
        self,
    ) -> None:
        decisions_to_test = (
            (HumanDecision.APPROVE, None),
            (HumanDecision.REJECT, "Material rejeitado pelo especialista."),
        )
        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação após tentativa de follow-up.",
            requires_human_decision=True,
        )
        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        for decision, justification in decisions_to_test:
            with self.subTest(decision=decision):
                predecessor = self.build_workflow(
                    workflow_id="wf-001",
                    opened_at=self.opened_at,
                )
                review = self.build_review(
                    review_id="rev-001",
                    human_decision=decision,
                    justification=justification,
                    corrections=(),
                    reviewed_at=self.reviewed_at,
                )
                concluded_predecessor = (
                    workflow_module.conclude_governance_workflow(
                        predecessor, review
                    )
                )
                self.assertEqual(
                    concluded_predecessor.status,
                    WorkflowStatus.REVIEWED,
                )

                with self.assertRaises(ValueError):
                    workflow_module.open_correction_follow_up(
                        concluded_predecessor,
                        workflow_id="wf-002",
                        recommendation=follow_up_recommendation,
                        opened_at=follow_up_opened_at,
                    )

    def test_open_correction_follow_up_rejects_predecessor_workflow_id_reuse(
        self,
    ) -> None:
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=self.opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        review = self.build_review(
            review_id="rev-001",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=self.reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )
        self.assertEqual(
            concluded_predecessor.status,
            WorkflowStatus.REVIEWED,
        )

        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação após tentativa de reuso de ID.",
            requires_human_decision=True,
        )
        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            workflow_module.open_correction_follow_up(
                concluded_predecessor,
                workflow_id=concluded_predecessor.workflow_id,
                recommendation=follow_up_recommendation,
                opened_at=follow_up_opened_at,
            )

    def test_open_correction_follow_up_rejects_material_id_mismatch(
        self,
    ) -> None:
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=self.opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        review = self.build_review(
            review_id="rev-001",
            material_id="MAT-0044",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=self.reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )
        self.assertEqual(
            concluded_predecessor.status,
            WorkflowStatus.REVIEWED,
        )
        self.assertEqual(concluded_predecessor.material_id, "MAT-0044")

        different_material_recommendation = DecisionRecommendation(
            material_id="MAT-9999",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação com material_id divergente.",
            requires_human_decision=True,
        )
        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            workflow_module.open_correction_follow_up(
                concluded_predecessor,
                workflow_id="wf-002",
                recommendation=different_material_recommendation,
                opened_at=follow_up_opened_at,
            )

    def test_open_correction_follow_up_rejects_opened_at_before_predecessor_closed_at(
        self,
    ) -> None:
        predecessor_opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=predecessor_opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        predecessor_reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            30,
            0,
            tzinfo=timezone.utc,
        )
        review = self.build_review(
            review_id="rev-001",
            material_id="MAT-0044",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=predecessor_reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )
        self.assertEqual(
            concluded_predecessor.status,
            WorkflowStatus.REVIEWED,
        )
        self.assertEqual(
            concluded_predecessor.closed_at,
            predecessor_reviewed_at,
        )

        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação com timestamp inválido.",
            requires_human_decision=True,
        )
        earlier_opened_at = datetime(
            2026,
            8,
            18,
            10,
            29,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            workflow_module.open_correction_follow_up(
                concluded_predecessor,
                workflow_id="wf-002",
                recommendation=follow_up_recommendation,
                opened_at=earlier_opened_at,
            )

    def test_open_correction_follow_up_allows_opened_at_equal_to_predecessor_closed_at(
        self,
    ) -> None:
        predecessor_opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=predecessor_opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        predecessor_reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            30,
            0,
            tzinfo=timezone.utc,
        )
        review = self.build_review(
            review_id="rev-001",
            material_id="MAT-0044",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=predecessor_reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )
        self.assertEqual(
            concluded_predecessor.status,
            WorkflowStatus.REVIEWED,
        )
        self.assertEqual(
            concluded_predecessor.closed_at,
            datetime(2026, 8, 18, 10, 30, 0, tzinfo=timezone.utc),
        )

        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação com timestamp idêntico ao encerramento.",
            requires_human_decision=True,
        )

        successor = workflow_module.open_correction_follow_up(
            concluded_predecessor,
            workflow_id="wf-002",
            recommendation=follow_up_recommendation,
            opened_at=concluded_predecessor.closed_at,
        )

        self.assertEqual(
            successor.opened_at,
            concluded_predecessor.closed_at,
        )
        self.assertEqual(
            successor.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertEqual(
            successor.predecessor_workflow_id,
            concluded_predecessor.workflow_id,
        )
        self.assertEqual(
            successor.triggering_review_id,
            concluded_predecessor.review.review_id,
        )

    def test_conclude_correction_follow_up_preserves_causal_lineage(
        self,
    ) -> None:
        predecessor_opened_at = datetime(
            2026,
            8,
            18,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=predecessor_opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        predecessor_reviewed_at = datetime(
            2026,
            8,
            18,
            10,
            30,
            0,
            tzinfo=timezone.utc,
        )
        predecessor_review = self.build_review(
            review_id="rev-001",
            material_id="MAT-0044",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=predecessor_reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, predecessor_review
        )

        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )
        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação para ciclo de follow-up após solicitação de correção.",
            requires_human_decision=True,
        )
        successor = workflow_module.open_correction_follow_up(
            concluded_predecessor,
            workflow_id="wf-002",
            recommendation=follow_up_recommendation,
            opened_at=follow_up_opened_at,
        )
        self.assertEqual(
            successor.predecessor_workflow_id,
            concluded_predecessor.workflow_id,
        )
        self.assertEqual(
            successor.triggering_review_id,
            predecessor_review.review_id,
        )

        successor_reviewed_at = datetime(
            2026,
            8,
            18,
            11,
            30,
            0,
            tzinfo=timezone.utc,
        )
        successor_review = self.build_review(
            review_id="rev-002",
            material_id="MAT-0044",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            justification="Novo ciclo revisado e aprovado pelo especialista.",
            corrections=(),
            reviewed_at=successor_reviewed_at,
        )

        concluded_successor = workflow_module.conclude_governance_workflow(
            successor, successor_review
        )

        self.assertEqual(
            concluded_successor.status,
            WorkflowStatus.REVIEWED,
        )
        self.assertEqual(
            concluded_successor.predecessor_workflow_id,
            successor.predecessor_workflow_id,
        )
        self.assertEqual(
            concluded_successor.triggering_review_id,
            successor.triggering_review_id,
        )

    def test_open_correction_follow_up_rejects_predecessor_workflow_id_reuse_with_surrounding_whitespace(
        self,
    ) -> None:
        predecessor = self.build_workflow(
            workflow_id="wf-001",
            opened_at=self.opened_at,
        )
        correction = CorrectionRequest(
            field_name="description",
            reason="Descrição incompleta",
            suggested_value="PARAFUSO SEXTAVADO M8X25 INOX A2",
        )
        review = self.build_review(
            review_id="rev-001",
            human_decision=HumanDecision.REQUEST_CORRECTION,
            justification="Necessário ajuste na descrição cadastrada.",
            corrections=(correction,),
            reviewed_at=self.reviewed_at,
        )
        concluded_predecessor = workflow_module.conclude_governance_workflow(
            predecessor, review
        )
        self.assertEqual(
            concluded_predecessor.status,
            WorkflowStatus.REVIEWED,
        )

        follow_up_recommendation = DecisionRecommendation(
            material_id="MAT-0044",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Nova recomendação após tentativa de reuso com whitespace.",
            requires_human_decision=True,
        )
        follow_up_opened_at = datetime(
            2026,
            8,
            18,
            11,
            0,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            workflow_module.open_correction_follow_up(
                concluded_predecessor,
                workflow_id="  wf-001  ",
                recommendation=follow_up_recommendation,
                opened_at=follow_up_opened_at,
            )

    def test_governance_workflow_rejects_blank_causal_lineage_ids(
        self,
    ) -> None:
        invalid_cases = (
            ("predecessor_whitespace", "   ", "rev-001"),
            ("predecessor_empty", "", "rev-001"),
            ("triggering_whitespace", "wf-001", "   "),
            ("triggering_empty", "wf-001", ""),
        )

        for case_name, pred_id, trig_id in invalid_cases:
            with self.subTest(case=case_name):
                with self.assertRaises(ValueError):
                    self.build_workflow(
                        predecessor_workflow_id=pred_id,
                        triggering_review_id=trig_id,
                    )


if __name__ == "__main__":
    unittest.main()
