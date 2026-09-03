from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab import (
    HumanReviewClaim,
    HumanReviewClaimFactState,
    HumanReviewClaimState,
    JsonlHumanReviewClaimRepository,
    project_human_review_claim_state,
)
from agent_lab.human_review import VerifiedSpecialistIdentity


class HumanReviewClaimProjectionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name) / "claims.jsonl"

        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="spec1@corp.local",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-002",
            identity_provider="CORP_IDP",
            identity_subject="spec2@corp.local",
            verification_id="VER-002",
            verified_at=datetime(2026, 9, 2, 9, 5, 0, tzinfo=timezone.utc),
        )

        # Claims com claimed_at deliberadamente desalinhados da ordem física de append:
        # 1o append: WF-001 / CLM-003 / 09:30
        self.claim_wf1_c = HumanReviewClaim(
            claim_id="CLM-003",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc),
        )
        # 2o append: WF-OTHER / CLM-999 / 09:15
        self.claim_other = HumanReviewClaim(
            claim_id="CLM-999",
            workflow_id="WF-OTHER",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 2, 9, 15, 0, tzinfo=timezone.utc),
        )
        # 3o append: WF-001 / CLM-001 / 09:10
        self.claim_wf1_a = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 9, 2, 9, 10, 0, tzinfo=timezone.utc),
        )
        # 4o append: WF-001 / CLM-002 / 09:20
        self.claim_wf1_b = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 9, 2, 9, 20, 0, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_vertical_claim_persistence_post_restart_and_canonical_projection(
        self,
    ) -> None:
        physical_append_sequence = (
            self.claim_wf1_c,
            self.claim_other,
            self.claim_wf1_a,
            self.claim_wf1_b,
        )

        # 1. Persistência pré-restart via JsonlHumanReviewClaimRepository
        repo_before_restart = JsonlHumanReviewClaimRepository(self.repo_path)
        for claim in physical_append_sequence:
            repo_before_restart.append(claim)

        # Provar que a ordem física de append é fielmente preservada pelo Repository
        claims_before_restart = repo_before_restart.list_all()
        self.assertEqual(
            claims_before_restart,
            physical_append_sequence,
        )

        # 2. Simulação de reinicialização de processo (nova instância sobre o mesmo arquivo)
        repo_after_restart = JsonlHumanReviewClaimRepository(self.repo_path)
        rehydrated_claims = repo_after_restart.list_all()

        # Repository preserva: a lista rehidratada reflete estritamente a ordem de append
        self.assertEqual(
            rehydrated_claims,
            physical_append_sequence,
        )

        # 3. Projeção pura sobre os fatos rehidratados pós-restart
        state = project_human_review_claim_state("WF-001", rehydrated_claims)

        # Projection interpreta: estado factual derivado estritamente
        self.assertIsInstance(state, HumanReviewClaimState)
        self.assertEqual(state.workflow_id, "WF-001")
        self.assertEqual(state.claim_count, 3)
        self.assertIs(state.state, HumanReviewClaimFactState.MULTIPLE_CLAIMS)
        self.assertTrue(state.has_claims)
        self.assertTrue(state.has_multiple_claims)
        self.assertFalse(state.is_unclaimed)
        self.assertIsNone(state.sole_claim)

        # O claim de outro workflow não faz parte do read-model
        self.assertNotIn(self.claim_other, state.claims)

        # Invariante arquitetural: Repository preserva ordem física (c, other, a, b),
        # mas Projection produz ordem canônica estrita (a, b, c) por (claimed_at ASC, claim_id ASC)
        expected_canonical_tuple = (
            self.claim_wf1_a,
            self.claim_wf1_b,
            self.claim_wf1_c,
        )
        self.assertEqual(state.claims, expected_canonical_tuple)

    def test_vertical_projection_for_unclaimed_workflow_post_restart(self) -> None:
        repo_before_restart = JsonlHumanReviewClaimRepository(self.repo_path)
        repo_before_restart.append(self.claim_other)

        repo_after_restart = JsonlHumanReviewClaimRepository(self.repo_path)
        rehydrated = repo_after_restart.list_all()

        state = project_human_review_claim_state("WF-UNCLAIMED", rehydrated)

        self.assertEqual(state.workflow_id, "WF-UNCLAIMED")
        self.assertEqual(state.claim_count, 0)
        self.assertIs(state.state, HumanReviewClaimFactState.NO_CLAIM)
        self.assertTrue(state.is_unclaimed)
        self.assertFalse(state.has_claims)
        self.assertFalse(state.has_multiple_claims)
        self.assertIsNone(state.sole_claim)
        self.assertEqual(state.claims, ())


if __name__ == "__main__":
    unittest.main()
