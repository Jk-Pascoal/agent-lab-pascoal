from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
)
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    ReleaseAwareClaimState,
)
from agent_lab.human_review_claim_release_repository import (
    JsonlHumanReviewClaimReleaseRepository,
)
from agent_lab.human_review_claim_repository import JsonlHumanReviewClaimRepository
from agent_lab.pending_human_reviews_with_claim_state_use_case import (
    ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase,
    PendingHumanReviewWithReleaseAwareClaimStateItem,
)
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class PendingHumanReviewsWithReleaseAwareClaimStateUseCaseIntegrationTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lifecycle_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        self.claim_path = Path(self.temp_dir.name) / "claims.jsonl"
        self.release_path = Path(self.temp_dir.name) / "claim_releases.jsonl"

        self.recommendation = DecisionRecommendation(
            material_id="MAT-INT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Revisão necessária para teste vertical de integração release-aware",
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

    def test_list_pending_human_reviews_with_release_aware_claim_state_post_restart(
        self,
    ) -> None:
        # 1. Instanciar os 3 repositories JSONL reais para a sessão de escrita
        lifecycle_repo_session1 = JsonlWorkflowLifecycleRepository(
            self.lifecycle_path
        )
        claim_repo_session1 = JsonlHumanReviewClaimRepository(self.claim_path)
        release_repo_session1 = JsonlHumanReviewClaimReleaseRepository(
            self.release_path
        )

        # ---------------------------------------------------------------------
        # Cenário A: WF-FULLY-RELEASED (aberto às 10:00 UTC, claim às 10:05, release às 10:10)
        # ---------------------------------------------------------------------
        opened_a = WorkflowOpened(
            event_id="evt-open-rel",
            workflow_id="WF-FULLY-RELEASED",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_a)

        claim_a_rel = HumanReviewClaim(
            claim_id="clm-rel-001",
            workflow_id="WF-FULLY-RELEASED",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 10, 5, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_a_rel)

        release_a_rel = HumanReviewClaimRelease(
            release_id="rel-rel-001",
            claim_id="clm-rel-001",
            workflow_id="WF-FULLY-RELEASED",
            released_by=self.specialist_1,
            released_at=datetime(2026, 9, 4, 10, 10, 0, tzinfo=timezone.utc),
        )
        release_repo_session1.append(release_a_rel)

        # ---------------------------------------------------------------------
        # Cenário B: WF-RECLAIMED (aberto às 10:15 UTC, claim A às 10:20,
        # release A às 10:25, claim B às 10:30) - Cenário Central Issue #145
        # ---------------------------------------------------------------------
        opened_b = WorkflowOpened(
            event_id="evt-open-reclaim",
            workflow_id="WF-RECLAIMED",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 15, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_b)

        claim_b_1 = HumanReviewClaim(
            claim_id="clm-rec-001",
            workflow_id="WF-RECLAIMED",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 10, 20, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_b_1)

        release_b_1 = HumanReviewClaimRelease(
            release_id="rel-rec-001",
            claim_id="clm-rec-001",
            workflow_id="WF-RECLAIMED",
            released_by=self.specialist_1,
            released_at=datetime(2026, 9, 4, 10, 25, 0, tzinfo=timezone.utc),
        )
        release_repo_session1.append(release_b_1)

        claim_b_2 = HumanReviewClaim(
            claim_id="clm-rec-002",
            workflow_id="WF-RECLAIMED",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 4, 10, 30, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_b_2)

        # ---------------------------------------------------------------------
        # Cenário C: WF-MULTIPLE-UNRELEASED (aberto às 10:35 UTC, claim A às 10:40,
        # claim B às 10:45, zero releases)
        # ---------------------------------------------------------------------
        opened_c = WorkflowOpened(
            event_id="evt-open-multi-unrel",
            workflow_id="WF-MULTIPLE-UNRELEASED",
            recommendation=self.recommendation,
            opened_at=datetime(2026, 9, 4, 10, 35, 0, tzinfo=timezone.utc),
        )
        lifecycle_repo_session1.append_opened(opened_c)

        claim_c_1 = HumanReviewClaim(
            claim_id="clm-mul-001",
            workflow_id="WF-MULTIPLE-UNRELEASED",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 4, 10, 40, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_c_1)

        claim_c_2 = HumanReviewClaim(
            claim_id="clm-mul-002",
            workflow_id="WF-MULTIPLE-UNRELEASED",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 4, 10, 45, 0, tzinfo=timezone.utc),
        )
        claim_repo_session1.append(claim_c_2)

        # 2. Descarte total das instâncias da sessão 1 (simulação de restart)
        del lifecycle_repo_session1
        del claim_repo_session1
        del release_repo_session1

        # 3. Criação de NOVAS instâncias sobre os mesmos arquivos físicos
        lifecycle_repo_restarted = JsonlWorkflowLifecycleRepository(
            self.lifecycle_path
        )
        claim_repo_restarted = JsonlHumanReviewClaimRepository(self.claim_path)
        release_repo_restarted = JsonlHumanReviewClaimReleaseRepository(
            self.release_path
        )

        # 4. Execução do caso de uso sobre as instâncias reidratadas
        use_case = ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase(
            workflow_lifecycle_repository=lifecycle_repo_restarted,
            claim_repository=claim_repo_restarted,
            claim_release_repository=release_repo_restarted,
        )
        result = use_case.execute()

        # ---------------------------------------------------------------------
        # Asserções de integridade vertical pós-restart
        # ---------------------------------------------------------------------
        # Contagem e ordem canônica FIFO (opened_at ASC, workflow_id ASC)
        self.assertEqual(len(result), 3)
        ordered_ids = [item.workflow.workflow_id for item in result]
        self.assertEqual(
            ordered_ids,
            ["WF-FULLY-RELEASED", "WF-RECLAIMED", "WF-MULTIPLE-UNRELEASED"],
        )

        # Asserções estruturais para todos os itens da fila
        for item in result:
            self.assertIsInstance(
                item, PendingHumanReviewWithReleaseAwareClaimStateItem
            )
            self.assertIsInstance(item.claim_state, ReleaseAwareClaimState)
            self.assertIs(
                item.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
            )
            self.assertEqual(
                item.workflow.workflow_id, item.claim_state.workflow_id
            )

        # 5. WF-FULLY-RELEASED -> história preservada, unreleased = NO_CLAIM
        item_rel = result[0]
        self.assertEqual(item_rel.workflow.workflow_id, "WF-FULLY-RELEASED")
        self.assertEqual(item_rel.claim_state.all_claims, (claim_a_rel,))
        self.assertEqual(item_rel.claim_state.releases, (release_a_rel,))
        self.assertEqual(item_rel.claim_state.unreleased_claims, ())
        self.assertEqual(item_rel.claim_state.all_claims_count, 1)
        self.assertEqual(item_rel.claim_state.releases_count, 1)
        self.assertEqual(item_rel.claim_state.unreleased_claim_count, 0)
        self.assertIs(
            item_rel.claim_state.unreleased_claim_state,
            HumanReviewClaimFactState.NO_CLAIM,
        )
        self.assertIsNone(item_rel.claim_state.sole_unreleased_claim)
        self.assertFalse(item_rel.claim_state.has_unreleased_claims)
        self.assertTrue(item_rel.claim_state.has_no_unreleased_claims)
        self.assertFalse(item_rel.claim_state.has_multiple_unreleased_claims)

        # 6. WF-RECLAIMED -> Cenário Central da Issue #145:
        # claim A + release A + claim B = SINGLE_CLAIM
        # (claim B é o único claim não liberado / sole_unreleased_claim)
        item_rec = result[1]
        self.assertEqual(item_rec.workflow.workflow_id, "WF-RECLAIMED")
        self.assertEqual(
            item_rec.claim_state.all_claims, (claim_b_1, claim_b_2)
        )
        self.assertEqual(item_rec.claim_state.releases, (release_b_1,))
        self.assertEqual(item_rec.claim_state.unreleased_claims, (claim_b_2,))
        self.assertEqual(item_rec.claim_state.all_claims_count, 2)
        self.assertEqual(item_rec.claim_state.releases_count, 1)
        self.assertEqual(item_rec.claim_state.unreleased_claim_count, 1)
        self.assertIs(
            item_rec.claim_state.unreleased_claim_state,
            HumanReviewClaimFactState.SINGLE_CLAIM,
        )
        self.assertEqual(item_rec.claim_state.sole_unreleased_claim, claim_b_2)
        self.assertTrue(item_rec.claim_state.has_unreleased_claims)
        self.assertFalse(item_rec.claim_state.has_no_unreleased_claims)
        self.assertFalse(item_rec.claim_state.has_multiple_unreleased_claims)

        # 7. WF-MULTIPLE-UNRELEASED -> MULTIPLE_CLAIMS
        item_mul = result[2]
        self.assertEqual(
            item_mul.workflow.workflow_id, "WF-MULTIPLE-UNRELEASED"
        )
        self.assertEqual(
            item_mul.claim_state.all_claims, (claim_c_1, claim_c_2)
        )
        self.assertEqual(item_mul.claim_state.releases, ())
        self.assertEqual(
            item_mul.claim_state.unreleased_claims, (claim_c_1, claim_c_2)
        )
        self.assertEqual(item_mul.claim_state.all_claims_count, 2)
        self.assertEqual(item_mul.claim_state.releases_count, 0)
        self.assertEqual(item_mul.claim_state.unreleased_claim_count, 2)
        self.assertIs(
            item_mul.claim_state.unreleased_claim_state,
            HumanReviewClaimFactState.MULTIPLE_CLAIMS,
        )
        self.assertIsNone(item_mul.claim_state.sole_unreleased_claim)
        self.assertTrue(item_mul.claim_state.has_unreleased_claims)
        self.assertFalse(item_mul.claim_state.has_no_unreleased_claims)
        self.assertTrue(item_mul.claim_state.has_multiple_unreleased_claims)


if __name__ == "__main__":
    unittest.main()
