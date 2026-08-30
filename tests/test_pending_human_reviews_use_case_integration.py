from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_use_case import RecordHumanDecisionUseCase
from agent_lab.pending_human_reviews_use_case import (
    ListPendingHumanReviewsUseCase,
)
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository


class PendingHumanReviewsUseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        self.audit_path = Path(self.temp_dir.name) / "audit.jsonl"

        self.opened_at_1 = datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc)
        self.reviewed_at_1 = datetime(2026, 8, 30, 8, 30, 0, tzinfo=timezone.utc)
        self.opened_at_2 = datetime(2026, 8, 30, 9, 0, 0, tzinfo=timezone.utc)
        self.verified_at = datetime(2026, 8, 30, 7, 30, 0, tzinfo=timezone.utc)

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=(),
            rationale="Recomendação REVIEW",
            requires_human_decision=True,
        )
        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )
        self.review_1 = HumanReview(
            review_id="rev-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at_1,
            justification="Aprovado",
            corrections=(),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_list_pending_human_reviews_post_restart_with_real_jsonl_repository(
        self,
    ) -> None:
        # 1. Persistência de eventos via primeira instância do repositório
        repository_1 = JsonlWorkflowLifecycleRepository(self.file_path)

        opened_1 = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at_1,
        )
        concluded_1 = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id="wf-001",
            review=self.review_1,
        )
        opened_2 = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-002",
            recommendation=self.recommendation,
            opened_at=self.opened_at_2,
        )

        repository_1.append_opened(opened_1)
        repository_1.append_concluded(concluded_1)
        repository_1.append_opened(opened_2)

        # 2. Simulação de restart descartando a instância e criando nova sobre o mesmo arquivo JSONL
        del repository_1

        restarted_repository = JsonlWorkflowLifecycleRepository(self.file_path)

        # 3. Consulta através do caso de uso de aplicação sobre o repositório reinicializado
        use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=restarted_repository
        )
        queue = use_case.execute()

        # 4. Asserções de contrato observável
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].workflow_id, "wf-002")
        self.assertEqual(queue[0].status, WorkflowStatus.PENDING_HUMAN_REVIEW)

    def test_list_pending_human_reviews_composition_with_record_human_decision(
        self,
    ) -> None:
        audit_repository = JsonlAuditRepository(self.audit_path)
        lifecycle_repository = JsonlWorkflowLifecycleRepository(self.file_path)

        opened = WorkflowOpened(
            event_id="evt-open-100",
            workflow_id="wf-100",
            recommendation=self.recommendation,
            opened_at=self.opened_at_1,
        )
        lifecycle_repository.append_opened(opened)

        list_use_case = ListPendingHumanReviewsUseCase(
            workflow_lifecycle_repository=lifecycle_repository
        )

        # 1. Primeira listagem: workflow pendente aparece na fila
        pending_before = list_use_case.execute()
        self.assertEqual(len(pending_before), 1)
        self.assertEqual(pending_before[0].workflow_id, "wf-100")

        # 2. Deliberação humana utilizando o workflow obtido diretamente da listagem
        record_use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repository,
            workflow_lifecycle_repository=lifecycle_repository,
        )

        record_use_case.execute(
            pending_before[0],
            review_id="rev-100",
            audit_event_id="evt-aud-100",
            lifecycle_event_id="evt-conc-100",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at_1,
            justification=None,
            corrections=(),
        )

        # 3. Segunda listagem: o workflow deliberado desaparece da fila
        pending_after = list_use_case.execute()
        self.assertEqual(pending_after, ())


if __name__ == "__main__":
    unittest.main()
