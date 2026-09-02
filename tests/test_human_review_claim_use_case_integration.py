from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_repository import (
    JsonlHumanReviewClaimRepository,
)
from agent_lab.human_review_claim_use_case import RecordHumanReviewClaimUseCase
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


class RecordHumanReviewClaimUseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "human_review_claims.jsonl"

        self.verified_at = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 9, 2, 9, 30, 0, tzinfo=timezone.utc)
        self.claimed_at = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)

        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Necessária revisão cadastral",
            requires_human_decision=True,
        )

        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
            review=None,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_record_claim_persists_to_jsonl_and_recovers_after_restart(self) -> None:
        # 1. Primeira sessão: instanciar Use Case com repositório real
        repository_before_restart = JsonlHumanReviewClaimRepository(self.storage_path)
        use_case = RecordHumanReviewClaimUseCase(
            claim_repository=repository_before_restart
        )

        # 2. Executar claim válido
        result = use_case.execute(
            self.workflow,
            claim_id="CLM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

        # 3. Comprovar resultado do caso de uso
        self.assertIsInstance(result, HumanReviewClaim)
        self.assertEqual(result.claim_id, "CLM-001")
        self.assertEqual(result.workflow_id, "WF-001")
        self.assertEqual(result.specialist, self.specialist)
        self.assertEqual(result.claimed_at, self.claimed_at)

        # 4. Comprovar persistência física real em disco
        self.assertTrue(self.storage_path.exists())
        self.assertGreater(self.storage_path.stat().st_size, 0)

        # 5. Simular restart: descartar primeira instância e instanciar novo repositório
        del use_case
        del repository_before_restart

        repository_after_restart = JsonlHumanReviewClaimRepository(self.storage_path)

        # 6. Ler claim pós-restart pelo contrato público do repositório
        rehydrated = repository_after_restart.get_by_id("CLM-001")
        self.assertIsNotNone(rehydrated)
        assert rehydrated is not None

        self.assertIsInstance(rehydrated, HumanReviewClaim)
        self.assertEqual(rehydrated, result)
        self.assertEqual(rehydrated.claim_id, "CLM-001")
        self.assertEqual(rehydrated.workflow_id, "WF-001")
        self.assertEqual(rehydrated.specialist, self.specialist)
        self.assertEqual(rehydrated.claimed_at, self.claimed_at)

        self.assertEqual(
            repository_after_restart.list_by_workflow_id("WF-001"),
            (rehydrated,),
        )
        self.assertEqual(
            repository_after_restart.list_all(),
            (rehydrated,),
        )

        # 7. Workflow de entrada permanece estritamente inalterado
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW)
        self.assertIsNone(self.workflow.review)
        self.assertEqual(self.workflow.workflow_id, "WF-001")
        self.assertEqual(self.workflow.opened_at, self.opened_at)
