from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_projection import HumanReviewClaimFactState
from agent_lab.human_review_claim_repository import JsonlHumanReviewClaimRepository
from agent_lab.pending_human_reviews_with_claim_state_use_case import (
    ListPendingHumanReviewsWithClaimStateUseCase,
    PendingHumanReviewWithClaimStateItem,
)
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class PendingHumanReviewsWithClaimStateUseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lifecycle_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        self.claim_path = Path(self.temp_dir.name) / "claims.jsonl"

        self.recommendation = DecisionRecommendation(
            material_id="MAT-INT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Revisão necessária para teste vertical de integração",
            requires_human_decision=True,
        )

        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-INT-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist1@corp.local",
            verification_id="VER-INT-001",
            verified_at=datetime(2026, 9, 4, 8, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-INT-002",
            identity_provider="CORP_IDP",
            identity_subject="specialist2@corp.local",
            verification_id="VER-INT-002",
            verified_at=datetime(2026, 9, 4, 8, 5, 0, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_list_pending_human_reviews_with_claim_state_post_restart(self) -> None:
        # 1. Instanciar repositories JSONL reais para a sessão de escrita
        lifecycle_repo_session1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        claim_repo_session1 = JsonlHumanReviewClaimRepository(self.claim_path)

        # ---------------------------------------------------------------------
        # Cenário A: WF-NO-CLAIM (aberto às 10:00 UTC, sem claims)
        # ---------------------------------------------------------------------
        opened_no_claim = WorkflowOpened(
            event_id="evt-open-noclaim",
            workflow_id="WF-NO-CLAIM",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_no_claim)

        # ---------------------------------------------------------------------
        # Cenário B: WF-SINGLE (aberto às 10:15 UTC, 1 claim persistido)
        # ---------------------------------------------------------------------
        opened_single = WorkflowOpened(
            event_id="evt-open-single",
            workflow_id="WF-SINGLE",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 15, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_single)

        claim_single = HumanReviewClaim(
            claim_id="clm-single-001",
            workflow_id="WF-SINGLE",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 10, 20, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_single)

        # ---------------------------------------------------------------------
        # Cenário C: WF-MULTIPLE (aberto às 10:30 UTC, 2 claims persistidos)
        # ---------------------------------------------------------------------
        opened_multiple = WorkflowOpened(
            event_id="evt-open-multi",
            workflow_id="WF-MULTIPLE",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 30, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_multiple)

        claim_multi_1 = HumanReviewClaim(
            claim_id="clm-multi-001",
            workflow_id="WF-MULTIPLE",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 10, 35, 0, tzinfo=timezone.utc),
        )
        claim_multi_2 = HumanReviewClaim(
            claim_id="clm-multi-002",
            workflow_id="WF-MULTIPLE",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 4, 10, 40, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_multi_1)
        claim_repo_session1.append(claim_multi_2)

        # ---------------------------------------------------------------------
        # Cenário D: WF-REVIEWED (aberto às 09:00 UTC, com claim, concluído às 09:30 UTC)
        # ---------------------------------------------------------------------
        opened_reviewed = WorkflowOpened(
            event_id="evt-open-rev",
            workflow_id="WF-REVIEWED",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 9, 0, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_reviewed)

        claim_reviewed = HumanReviewClaim(
            claim_id="clm-rev-001",
            workflow_id="WF-REVIEWED",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 9, 10, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_reviewed)

        review_completed = HumanReview(
            review_id="rev-int-001",
            material_id="MAT-INT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.specialist_1,
            reviewed_at=datetime(2026, 9, 4, 9, 30, 0, tzinfo=timezone.utc),
            justification="Aprovado no fluxo formal de revisão",
            corrections=(),
        )
        concluded_reviewed = WorkflowConcluded(
            event_id="evt-conc-rev",
            workflow_id="WF-REVIEWED",
            review=review_completed,
        )
        lifecycle_repo_session1.append_concluded(concluded_reviewed)

        # 2. Simulação de restart: descartar completamente as instâncias de escrita
        del lifecycle_repo_session1
        del claim_repo_session1

        # 3. Criar NOVAS instâncias dos repositories JSONL sobre os mesmos arquivos físicos
        lifecycle_repo_restarted = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        claim_repo_restarted = JsonlHumanReviewClaimRepository(self.claim_path)

        # 4. Executar o caso de uso com as novas instâncias reidratadas do disco
        use_case = ListPendingHumanReviewsWithClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo_restarted,
            claim_repository=claim_repo_restarted,
        )
        result = use_case.execute()

        # ---------------------------------------------------------------------
        # Verificações de integridade vertical pós-restart:
        # ---------------------------------------------------------------------
        # 1. Exatamente 3 workflows pendentes
        self.assertEqual(len(result), 3)

        # 2. Ordem estritamente canônica FIFO (opened_at ASC, workflow_id ASC)
        ordered_ids = [item.workflow.workflow_id for item in result]
        self.assertEqual(ordered_ids, ["WF-NO-CLAIM", "WF-SINGLE", "WF-MULTIPLE"])

        # 3. WF-REVIEWED não aparece na fila
        self.assertNotIn("WF-REVIEWED", ordered_ids)

        # 4. Todos os itens são instâncias imutáveis e possuem alinhamento relacional
        for item in result:
            self.assertIsInstance(item, PendingHumanReviewWithClaimStateItem)
            self.assertEqual(item.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
            self.assertEqual(item.workflow.workflow_id, item.claim_state.workflow_id)

        # 5. WF-NO-CLAIM -> NO_CLAIM
        item_no_claim = result[0]
        self.assertEqual(item_no_claim.workflow.workflow_id, "WF-NO-CLAIM")
        self.assertEqual(item_no_claim.claim_state.state, HumanReviewClaimFactState.NO_CLAIM)
        self.assertTrue(item_no_claim.claim_state.is_unclaimed)
        self.assertFalse(item_no_claim.claim_state.has_claims)
        self.assertFalse(item_no_claim.claim_state.has_multiple_claims)
        self.assertEqual(item_no_claim.claim_state.claim_count, 0)
        self.assertIsNone(item_no_claim.claim_state.sole_claim)

        # 6. WF-SINGLE -> SINGLE_CLAIM
        item_single = result[1]
        self.assertEqual(item_single.workflow.workflow_id, "WF-SINGLE")
        self.assertEqual(item_single.claim_state.state, HumanReviewClaimFactState.SINGLE_CLAIM)
        self.assertFalse(item_single.claim_state.is_unclaimed)
        self.assertTrue(item_single.claim_state.has_claims)
        self.assertFalse(item_single.claim_state.has_multiple_claims)
        self.assertEqual(item_single.claim_state.claim_count, 1)
        self.assertEqual(item_single.claim_state.sole_claim, claim_single)

        # 7. WF-MULTIPLE -> MULTIPLE_CLAIMS
        item_multiple = result[2]
        self.assertEqual(item_multiple.workflow.workflow_id, "WF-MULTIPLE")
        self.assertEqual(item_multiple.claim_state.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertFalse(item_multiple.claim_state.is_unclaimed)
        self.assertTrue(item_multiple.claim_state.has_claims)
        self.assertTrue(item_multiple.claim_state.has_multiple_claims)
        self.assertEqual(item_multiple.claim_state.claim_count, 2)
        self.assertIsNone(item_multiple.claim_state.sole_claim)
        self.assertEqual(
            item_multiple.claim_state.claims,
            (claim_multi_1, claim_multi_2),
        )


if __name__ == "__main__":
    unittest.main()
