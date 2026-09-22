from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from agent_lab.audit_repository import JsonlAuditRepository
from agent_lab.consistency import verify_repositories_consistency
from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    HumanDecision,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_claim import claim_pending_human_review
from agent_lab.human_review_claim_release_repository import (
    JsonlHumanReviewClaimReleaseRepository,
)
from agent_lab.human_review_claim_repository import (
    HumanReviewClaimCorruptionError,
    JsonlHumanReviewClaimRepository,
)
from agent_lab.human_review_claim_use_case import (
    RecordHumanReviewClaimUseCase,
)
from agent_lab.human_review_use_case import (
    RecordHumanDecisionUseCase,
    ReviewerNotEligibleError,
)
from agent_lab.reviewer_eligibility_policy import ReviewerEligibilityStatus
from agent_lab.workflow import WorkflowStatus
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_projection import rehydrate_workflow
from agent_lab.workflow_repository import JsonlWorkflowLifecycleRepository
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
)
from agent_lab.human_review_claim_release_use_case import (
    ReleaseHumanReviewClaimUseCase,
)
from agent_lab.pending_human_reviews_with_claim_state_use_case import (
    ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase,
)


class HumanReviewUseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audit_path = Path(self.temp_dir.name) / "audit.jsonl"
        self.lifecycle_path = (
            Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        )
        self.claim_path = Path(self.temp_dir.name) / "claims.jsonl"
        self.release_path = Path(self.temp_dir.name) / "claim_releases.jsonl"

        self.verified_at = datetime(2026, 8, 28, 8, 0, 0, tzinfo=timezone.utc)
        self.opened_at = datetime(2026, 8, 28, 8, 30, 0, tzinfo=timezone.utc)
        self.claimed_at = datetime(2026, 8, 28, 9, 0, 0, tzinfo=timezone.utc)
        self.reviewed_at = datetime(2026, 8, 28, 9, 30, 0, tzinfo=timezone.utc)

        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="CORP_IDP",
            identity_subject="specialist@corp.local",
            verification_id="ver-001",
            verified_at=self.verified_at,
        )

        self.evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório pendente de validação.",
                severity=IssueSeverity.WARNING,
            ),
        )

        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence,
            rationale="Recomendação REVIEW para MAT-001",
            requires_human_decision=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_use_case_integration_with_real_jsonl_repositories_survives_restart_and_rehydrates_reviewed_state(
        self,
    ) -> None:
        # 1. Setup inicial de repositórios e abertura do workflow no lifecycle
        audit_repo_1 = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        opened = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo_1.append_opened(opened)

        # 2. Obtenção do workflow pendente via projeção
        events_opened = lifecycle_repo_1.get_events_by_workflow_id(
            "wf-mat-001-01"
        )
        pending_workflow = rehydrate_workflow(events_opened)
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        # 3. Execução do caso de uso de aplicação com repositórios reais
        claim_repo_1 = JsonlHumanReviewClaimRepository(self.claim_path)
        claim_1 = claim_pending_human_review(
            pending_workflow,
            claim_id="claim-mat-001-01",
            specialist=self.identity,
            claimed_at=self.claimed_at,
        )
        claim_repo_1.append(claim_1)

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo_1,
            workflow_lifecycle_repository=lifecycle_repo_1,
            claim_repository=claim_repo_1,
            claim_release_repository=JsonlHumanReviewClaimReleaseRepository(
                self.release_path
            ),
        )

        result = use_case.execute(
            pending_workflow,
            review_id="rev-001",
            audit_event_id="evt-aud-001",
            lifecycle_event_id="evt-conc-001",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        self.assertEqual(result.workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(result.review.human_decision, HumanDecision.APPROVE)

        # 4. Simulação de restart: descarte das instâncias e nova instanciação sobre os mesmos arquivos
        del audit_repo_1
        del lifecycle_repo_1
        del use_case

        audit_repo_2 = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_2 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        # 5. Comprovação da persistência física de auditoria após restart
        persisted_audit = audit_repo_2.get_by_id("evt-aud-001")
        self.assertIsNotNone(persisted_audit)
        self.assertEqual(persisted_audit, result.audit_event)

        # 6. Comprovação da persistência física e reidratação do ciclo de vida após restart
        events_after_restart = lifecycle_repo_2.get_events_by_workflow_id(
            "wf-mat-001-01"
        )
        self.assertEqual(len(events_after_restart), 2)
        self.assertEqual(events_after_restart[0], opened)
        self.assertEqual(events_after_restart[1], result.lifecycle_event)

        rehydrated_workflow = rehydrate_workflow(events_after_restart)
        self.assertEqual(rehydrated_workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(rehydrated_workflow.review, result.review)
        self.assertEqual(rehydrated_workflow.closed_at, self.reviewed_at)
        self.assertEqual(rehydrated_workflow.workflow_id, "wf-mat-001-01")
        self.assertEqual(rehydrated_workflow.material_id, "MAT-001")
        self.assertEqual(
            rehydrated_workflow.review_lead_time,
            self.reviewed_at - self.opened_at,
        )

    def test_use_case_integration_maintains_dual_write_consistency_report_clean(
        self,
    ) -> None:
        # 1. Setup de repositórios reais
        audit_repo = JsonlAuditRepository(self.audit_path)
        lifecycle_repo = JsonlWorkflowLifecycleRepository(self.lifecycle_path)

        opened = WorkflowOpened(
            event_id="evt-open-002",
            workflow_id="wf-mat-001-02",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo.append_opened(opened)

        pending_workflow = rehydrate_workflow(
            lifecycle_repo.get_events_by_workflow_id("wf-mat-001-02")
        )

        # 2. Execução do caso de uso
        claim_repo = JsonlHumanReviewClaimRepository(self.claim_path)
        claim_2 = claim_pending_human_review(
            pending_workflow,
            claim_id="claim-mat-001-02",
            specialist=self.identity,
            claimed_at=self.claimed_at,
        )
        claim_repo.append(claim_2)

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
            claim_release_repository=JsonlHumanReviewClaimReleaseRepository(
                self.release_path
            ),
        )

        use_case.execute(
            pending_workflow,
            review_id="rev-002",
            audit_event_id="evt-aud-002",
            lifecycle_event_id="evt-conc-002",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        # 3. Verificação de consistência cruzada dual-write pós-execução
        report = verify_repositories_consistency(
            lifecycle_repo=lifecycle_repo,
            audit_repo=audit_repo,
        )

        self.assertTrue(report.is_consistent)
        self.assertEqual(report.issue_count, 0)
        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())

    def test_persisted_claim_survives_restart_and_authorizes_human_decision(
        self,
    ) -> None:
        # 1. Setup inicial de repositórios reais e abertura do workflow
        lifecycle_repo = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        opened = WorkflowOpened(
            event_id="evt-open-restart-01",
            workflow_id="wf-restart-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo.append_opened(opened)

        # 2. Obtenção do workflow pendente real
        events_opened = lifecycle_repo.get_events_by_workflow_id(
            "wf-restart-01"
        )
        pending_workflow = rehydrate_workflow(events_opened)
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        # 3. Criação de claim real e persistência com primeira instância do repositório via use case
        claim_repo_1 = JsonlHumanReviewClaimRepository(self.claim_path)
        record_claim_use_case = RecordHumanReviewClaimUseCase(
            claim_repository=claim_repo_1,
        )
        claim = record_claim_use_case.execute(
            pending_workflow,
            claim_id="claim-restart-01",
            specialist=self.identity,
            claimed_at=self.claimed_at,
        )

        # 4. Descarte da instância do repositório de claims (simulando encerramento)
        del claim_repo_1

        # 5. Nova instância de repositório de claims apontando para o mesmo arquivo JSONL
        claim_repo_2 = JsonlHumanReviewClaimRepository(self.claim_path)
        audit_repo = JsonlAuditRepository(self.audit_path)

        # Comprovação de que o claim reidratado do disco é estruturalmente igual, mas não o mesmo objeto em memória
        rehydrated_claims = claim_repo_2.list_by_workflow_id("wf-restart-01")
        self.assertEqual(len(rehydrated_claims), 1)
        self.assertEqual(rehydrated_claims[0].claim_id, claim.claim_id)
        self.assertEqual(
            rehydrated_claims[0].specialist.specialist_id,
            self.identity.specialist_id,
        )
        self.assertIsNot(rehydrated_claims[0], claim)

        # 6. Execução da deliberação através do use case com a nova instância
        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo_2,
            claim_release_repository=JsonlHumanReviewClaimReleaseRepository(
                self.release_path
            ),
        )

        result = use_case.execute(
            pending_workflow,
            review_id="rev-restart-01",
            audit_event_id="evt-aud-restart-01",
            lifecycle_event_id="evt-conc-restart-01",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )

        # 7. Verificações de persistência física e integridade
        self.assertEqual(result.workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(result.review.human_decision, HumanDecision.APPROVE)

        persisted_audit = audit_repo.get_by_id("evt-aud-restart-01")
        self.assertIsNotNone(persisted_audit)
        self.assertEqual(persisted_audit, result.audit_event)

        events_after = lifecycle_repo.get_events_by_workflow_id("wf-restart-01")
        self.assertEqual(len(events_after), 2)
        self.assertIsInstance(events_after[1], WorkflowConcluded)
        self.assertEqual(events_after[1], result.lifecycle_event)

        rehydrated_workflow = rehydrate_workflow(events_after)
        self.assertEqual(rehydrated_workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(rehydrated_workflow.review, result.review)

        # 8. Verificação de consistência cruzada dual-write pós-execução
        report = verify_repositories_consistency(
            lifecycle_repo=lifecycle_repo,
            audit_repo=audit_repo,
        )
        self.assertTrue(report.is_consistent)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())

    def test_restart_without_claim_rejects_human_decision_and_preserves_opened_state(
        self,
    ) -> None:
        # 1. Persistência inicial de apenas WorkflowOpened em repositório real
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        opened = WorkflowOpened(
            event_id="evt-open-noclaim-01",
            workflow_id="wf-noclaim-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo_1.append_opened(opened)

        # 2. Simulação de restart descartando instâncias e recriando sobre os arquivos reais
        del lifecycle_repo_1

        audit_repo_restart = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_restart = JsonlWorkflowLifecycleRepository(
            self.lifecycle_path
        )
        claim_repo_restart = JsonlHumanReviewClaimRepository(self.claim_path)

        events_before = lifecycle_repo_restart.get_events_by_workflow_id(
            "wf-noclaim-01"
        )
        pending_workflow = rehydrate_workflow(events_before)
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        # 3. Execução da deliberação sem nenhum claim persistido
        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo_restart,
            workflow_lifecycle_repository=lifecycle_repo_restart,
            claim_repository=claim_repo_restart,
            claim_release_repository=JsonlHumanReviewClaimReleaseRepository(
                self.release_path
            ),
        )

        with self.assertRaises(ReviewerNotEligibleError) as ctx:
            use_case.execute(
                pending_workflow,
                review_id="rev-noclaim-01",
                audit_event_id="evt-aud-noclaim-01",
                lifecycle_event_id="evt-conc-noclaim-01",
                human_decision=HumanDecision.APPROVE,
                reviewer_identity=self.identity,
                reviewed_at=self.reviewed_at,
                justification=None,
                corrections=(),
            )

        self.assertEqual(
            ctx.exception.decision.status,
            ReviewerEligibilityStatus.CLAIM_REQUIRED,
        )

        # 4. Evidência persistente nos arquivos reais JSONL após a rejeição:
        # a) Audit: nenhum evento de auditoria gravado
        self.assertEqual(len(audit_repo_restart.list_all()), 0)
        self.assertIsNone(audit_repo_restart.get_by_id("evt-aud-noclaim-01"))

        # b) Lifecycle: permanece estritamente apenas o WorkflowOpened inicial
        events_after = lifecycle_repo_restart.get_events_by_workflow_id(
            "wf-noclaim-01"
        )
        self.assertEqual(len(events_after), 1)
        self.assertEqual(events_after[0], opened)
        self.assertFalse(
            any(isinstance(e, WorkflowConcluded) for e in events_after)
        )

        # c) Claims: continua vazio
        self.assertEqual(
            claim_repo_restart.list_by_workflow_id("wf-noclaim-01"), ()
        )

        # d) Workflow reidratado permanece no status PENDING_HUMAN_REVIEW
        rehydrated_workflow = rehydrate_workflow(events_after)
        self.assertEqual(
            rehydrated_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(rehydrated_workflow.review)

    def test_corrupted_claim_jsonl_fails_closed_before_human_decision_writes(
        self,
    ) -> None:
        # 1. Setup inicial: workflow aberto em repositório real
        lifecycle_repo = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        opened = WorkflowOpened(
            event_id="evt-open-corrupt-01",
            workflow_id="wf-corrupt-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )
        lifecycle_repo.append_opened(opened)

        # 2. Obtenção do workflow pendente real
        events_opened = lifecycle_repo.get_events_by_workflow_id(
            "wf-corrupt-01"
        )
        pending_workflow = rehydrate_workflow(events_opened)
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        # 3. Criação física do arquivo de claims com conteúdo JSON corrompido
        self.claim_path.write_text(
            '{"schema_version": 1, "claim_id": \n',
            encoding="utf-8",
        )

        # 4. Nova instância do repositório de claims apontando para o arquivo corrompido
        claim_repo = JsonlHumanReviewClaimRepository(self.claim_path)
        audit_repo = JsonlAuditRepository(self.audit_path)

        use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo,
            workflow_lifecycle_repository=lifecycle_repo,
            claim_repository=claim_repo,
            claim_release_repository=JsonlHumanReviewClaimReleaseRepository(
                self.release_path
            ),
        )

        # 5. Execução do caso de uso falha com a exceção real de corrupção do repositório
        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            use_case.execute(
                pending_workflow,
                review_id="rev-corrupt-01",
                audit_event_id="evt-aud-corrupt-01",
                lifecycle_event_id="evt-conc-corrupt-01",
                human_decision=HumanDecision.APPROVE,
                reviewer_identity=self.identity,
                reviewed_at=self.reviewed_at,
                justification=None,
                corrections=(),
            )

        self.assertEqual(ctx.exception.line_number, 1)

        # 6. Comprovação física de fail-closed e zero escritas nos repositórios:
        # a) Audit: nenhum evento gravado
        self.assertEqual(len(audit_repo.list_all()), 0)
        self.assertIsNone(audit_repo.get_by_id("evt-aud-corrupt-01"))

        # b) Lifecycle: permanece estritamente apenas o WorkflowOpened inicial
        events_after = lifecycle_repo.get_events_by_workflow_id(
            "wf-corrupt-01"
        )
        self.assertEqual(len(events_after), 1)
        self.assertEqual(events_after[0], opened)
        self.assertFalse(
            any(isinstance(e, WorkflowConcluded) for e in events_after)
        )

        # c) Workflow reidratado permanece no status PENDING_HUMAN_REVIEW
        rehydrated_workflow = rehydrate_workflow(events_after)
        self.assertEqual(
            rehydrated_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(rehydrated_workflow.review)

    def test_release_aware_claim_handoff_survives_restart_and_allows_new_claimant_decision(
        self,
    ) -> None:
        # 1. Linha temporal estritamente causal e timezone-aware UTC
        opened_at = datetime(2026, 8, 28, 8, 30, 0, tzinfo=timezone.utc)
        claim_a_at = datetime(2026, 8, 28, 9, 0, 0, tzinfo=timezone.utc)
        release_a_at = datetime(2026, 8, 28, 9, 10, 0, tzinfo=timezone.utc)
        claim_b_at = datetime(2026, 8, 28, 9, 20, 0, tzinfo=timezone.utc)
        reviewed_at = datetime(2026, 8, 28, 9, 30, 0, tzinfo=timezone.utc)

        # 2. Identidades com Stable Principals distintos
        specialist_a = VerifiedSpecialistIdentity(
            specialist_id="spec-handoff-a",
            identity_provider="CORP_IDP",
            identity_subject="specialist.a@corp.local",
            verification_id="ver-handoff-a",
            verified_at=datetime(2026, 8, 28, 8, 0, 0, tzinfo=timezone.utc),
        )
        specialist_b = VerifiedSpecialistIdentity(
            specialist_id="spec-handoff-b",
            identity_provider="CORP_IDP",
            identity_subject="specialist.b@corp.local",
            verification_id="ver-handoff-b",
            verified_at=datetime(2026, 8, 28, 8, 5, 0, tzinfo=timezone.utc),
        )
        specialist_c = VerifiedSpecialistIdentity(
            specialist_id="spec-handoff-c",
            identity_provider="CORP_IDP",
            identity_subject="specialist.c@corp.local",
            verification_id="ver-handoff-c",
            verified_at=datetime(2026, 8, 28, 8, 10, 0, tzinfo=timezone.utc),
        )

        workflow_id = "wf-release-aware-handoff-01"
        opened = WorkflowOpened(
            event_id="evt-open-handoff-01",
            workflow_id=workflow_id,
            recommendation=self.recommendation,
            opened_at=opened_at,
        )

        # 3. Sessão 1 de escrita: uso exclusivo dos Casos de Uso de Aplicação reais
        audit_repo_1 = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_1 = JsonlWorkflowLifecycleRepository(self.lifecycle_path)
        claim_repo_1 = JsonlHumanReviewClaimRepository(self.claim_path)
        release_repo_1 = JsonlHumanReviewClaimReleaseRepository(
            self.release_path
        )

        lifecycle_repo_1.append_opened(opened)
        pending_workflow = rehydrate_workflow(
            lifecycle_repo_1.get_events_by_workflow_id(workflow_id)
        )
        self.assertEqual(
            pending_workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )

        record_claim_use_case_1 = RecordHumanReviewClaimUseCase(
            claim_repository=claim_repo_1
        )
        release_claim_use_case_1 = ReleaseHumanReviewClaimUseCase(
            claim_release_repository=release_repo_1
        )

        # Especialista A assume o claim
        claim_a = record_claim_use_case_1.execute(
            pending_workflow,
            claim_id="claim-handoff-a",
            specialist=specialist_a,
            claimed_at=claim_a_at,
        )

        # Especialista A libera o claim
        release_a = release_claim_use_case_1.execute(
            pending_workflow,
            claim_a,
            release_id="rel-handoff-a",
            releasing_specialist=specialist_a,
            released_at=release_a_at,
        )

        # Especialista B assume novo claim para o workflow
        claim_b = record_claim_use_case_1.execute(
            pending_workflow,
            claim_id="claim-handoff-b",
            specialist=specialist_b,
            claimed_at=claim_b_at,
        )

        self.assertEqual(
            claim_repo_1.list_by_workflow_id(workflow_id), (claim_a, claim_b)
        )
        self.assertEqual(
            release_repo_1.list_by_workflow_id(workflow_id), (release_a,)
        )

        # 4. Primeiro Restart: descarte total das instâncias e reconstrução sobre os arquivos físicos JSONL
        del audit_repo_1
        del lifecycle_repo_1
        del claim_repo_1
        del release_repo_1
        del record_claim_use_case_1
        del release_claim_use_case_1

        audit_repo_restarted = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_restarted = JsonlWorkflowLifecycleRepository(
            self.lifecycle_path
        )
        claim_repo_restarted = JsonlHumanReviewClaimRepository(self.claim_path)
        release_repo_restarted = JsonlHumanReviewClaimReleaseRepository(
            self.release_path
        )

        workflow_after_restart = rehydrate_workflow(
            lifecycle_repo_restarted.get_events_by_workflow_id(workflow_id)
        )
        self.assertEqual(
            workflow_after_restart.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(workflow_after_restart.review)

        # 5. Consulta da Pending Queue release-aware pós-restart
        queue_use_case = (
            ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase(
                workflow_lifecycle_repository=lifecycle_repo_restarted,
                claim_repository=claim_repo_restarted,
                claim_release_repository=release_repo_restarted,
            )
        )
        queue_items = queue_use_case.execute()
        self.assertEqual(len(queue_items), 1)

        item = queue_items[0]
        self.assertEqual(item.workflow.workflow_id, workflow_id)
        self.assertEqual(
            item.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertEqual(item.claim_state.all_claims, (claim_a, claim_b))
        self.assertEqual(item.claim_state.releases, (release_a,))
        # claim A + release A + claim B = SINGLE_CLAIM sobre unreleased_claims, preservando integralmente a história
        self.assertEqual(item.claim_state.unreleased_claims, (claim_b,))
        self.assertEqual(item.claim_state.all_claims_count, 2)
        self.assertEqual(item.claim_state.releases_count, 1)
        self.assertEqual(item.claim_state.unreleased_claim_count, 1)
        self.assertIs(
            item.claim_state.unreleased_claim_state,
            HumanReviewClaimFactState.SINGLE_CLAIM,
        )
        self.assertEqual(item.claim_state.sole_unreleased_claim, claim_b)
        self.assertTrue(item.claim_state.has_unreleased_claims)
        self.assertFalse(item.claim_state.has_no_unreleased_claims)
        self.assertFalse(item.claim_state.has_multiple_unreleased_claims)

        # 6. Tentativa de decisão por Especialista C rejeitada fail-closed (CLAIMANT_MISMATCH)
        decision_use_case = RecordHumanDecisionUseCase(
            audit_repository=audit_repo_restarted,
            workflow_lifecycle_repository=lifecycle_repo_restarted,
            claim_repository=claim_repo_restarted,
            claim_release_repository=release_repo_restarted,
        )

        with self.assertRaises(ReviewerNotEligibleError) as ctx:
            decision_use_case.execute(
                workflow_after_restart,
                review_id="rev-handoff-invalid",
                audit_event_id="evt-aud-release-aware-handoff-invalid",
                lifecycle_event_id="evt-conc-handoff-invalid",
                human_decision=HumanDecision.APPROVE,
                reviewer_identity=specialist_c,
                reviewed_at=reviewed_at,
                justification=None,
                corrections=(),
            )

        self.assertIs(
            ctx.exception.decision.status,
            ReviewerEligibilityStatus.CLAIMANT_MISMATCH,
        )
        self.assertFalse(ctx.exception.decision.is_eligible)

        # Comprovação física de zero writes após tentativa não elegível
        self.assertIsNone(
            audit_repo_restarted.get_by_id(
                "evt-aud-release-aware-handoff-invalid"
            )
        )
        events_after_invalid = (
            lifecycle_repo_restarted.get_events_by_workflow_id(workflow_id)
        )
        self.assertEqual(len(events_after_invalid), 1)
        self.assertEqual(events_after_invalid[0], opened)
        rehydrated_after_invalid = rehydrate_workflow(events_after_invalid)
        self.assertEqual(
            rehydrated_after_invalid.status,
            WorkflowStatus.PENDING_HUMAN_REVIEW,
        )
        self.assertIsNone(rehydrated_after_invalid.review)

        # 7. Deliberação válida submetida pelo Especialista B (sole unreleased claimant)
        result = decision_use_case.execute(
            workflow_after_restart,
            review_id="rev-handoff-valid",
            audit_event_id="evt-aud-handoff-valid",
            lifecycle_event_id="evt-conc-handoff-valid",
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=specialist_b,
            reviewed_at=reviewed_at,
            justification="Decisão fundamentada aprovada pelo especialista B.",
            corrections=(),
        )

        self.assertEqual(result.workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(result.review.human_decision, HumanDecision.APPROVE)
        self.assertEqual(result.review.reviewer_identity, specialist_b)
        self.assertEqual(result.review.reviewed_at, reviewed_at)

        # Repositórios de claims e releases permanecem intactos após a decisão
        self.assertEqual(
            claim_repo_restarted.list_by_workflow_id(workflow_id),
            (claim_a, claim_b),
        )
        self.assertEqual(
            release_repo_restarted.list_by_workflow_id(workflow_id),
            (release_a,),
        )

        # 8. Reinicialização Final: comprovação de persistência e reidratação definitiva pós-restart
        del audit_repo_restarted
        del lifecycle_repo_restarted
        del claim_repo_restarted
        del release_repo_restarted
        del decision_use_case
        del queue_use_case

        audit_repo_final = JsonlAuditRepository(self.audit_path)
        lifecycle_repo_final = JsonlWorkflowLifecycleRepository(
            self.lifecycle_path
        )
        claim_repo_final = JsonlHumanReviewClaimRepository(self.claim_path)
        release_repo_final = JsonlHumanReviewClaimReleaseRepository(
            self.release_path
        )

        # a) Auditoria física persistida e íntegra
        persisted_audit = audit_repo_final.get_by_id("evt-aud-handoff-valid")
        self.assertIsNotNone(persisted_audit)
        self.assertEqual(persisted_audit, result.audit_event)

        # b) Ciclo de vida persistido com WorkflowConcluded e status REVIEWED reidratado
        final_events = lifecycle_repo_final.get_events_by_workflow_id(
            workflow_id
        )
        self.assertEqual(len(final_events), 2)
        self.assertEqual(final_events[0], opened)
        self.assertEqual(final_events[1], result.lifecycle_event)

        final_workflow = rehydrate_workflow(final_events)
        self.assertEqual(final_workflow.status, WorkflowStatus.REVIEWED)
        self.assertEqual(final_workflow.review, result.review)
        self.assertEqual(final_workflow.closed_at, reviewed_at)

        # c) Claims e releases históricos persistem intactos e inalterados
        self.assertEqual(
            claim_repo_final.list_by_workflow_id(workflow_id),
            (claim_a, claim_b),
        )
        self.assertEqual(
            release_repo_final.list_by_workflow_id(workflow_id),
            (release_a,),
        )

        # d) Fila de workflows pendentes agora está vazia para este workflow
        final_queue_use_case = (
            ListPendingHumanReviewsWithReleaseAwareClaimStateUseCase(
                workflow_lifecycle_repository=lifecycle_repo_final,
                claim_repository=claim_repo_final,
                claim_release_repository=release_repo_final,
            )
        )
        self.assertEqual(final_queue_use_case.execute(), ())

        # e) Consistência cruzada dual-write Audit + Lifecycle validada
        report = verify_repositories_consistency(
            lifecycle_repo=lifecycle_repo_final,
            audit_repo=audit_repo_final,
        )
        self.assertTrue(report.is_consistent)
        self.assertEqual(report.issue_count, 0)
        self.assertEqual(report.total_concluded_events, 1)
        self.assertEqual(report.total_audit_review_events, 1)
        self.assertEqual(report.matched_pairs_count, 1)
        self.assertEqual(report.issues, ())


if __name__ == "__main__":
    unittest.main()
